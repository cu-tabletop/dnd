import logging
import asyncio
from aiogram import Router
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Group, Row, ListGroup, SwitchTo
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram.types import CallbackQuery

from services.api_client import api_client
import states.states as states

logger = logging.getLogger(__name__)


# === Геттеры ===
async def get_invite_data(message, dialog_manager: DialogManager, kwargs):
    owner_id = dialog_manager.start_data.get("owner_id")
    owner_name = dialog_manager.start_data.get("owner_name")
    campaign_id = dialog_manager.start_data.get("campaign_id")
    page = dialog_manager.dialog_data.get("page", 0)
    characters_per_page = 5

    # Параллельно запрашиваем информацию о кампании и персонажей
    campaign_task = api_client.get_campaign(campaign_id, owner_id)
    characters_task = api_client.get_characters(user_id=message.from_user.id)

    campaign, characters = await asyncio.gather(campaign_task, characters_task)

    dialog_manager.dialog_data["invite_campaign"] = campaign

    # Пагинация для персонажей
    if not characters:
        characters_data = {
            "characters": [],
            "current_page": 1,
            "total_pages": 1,
            "has_prev": False,
            "has_next": False,
            "has_characters": False,
        }
    else:
        start_idx = page * characters_per_page
        end_idx = start_idx + characters_per_page
        current_characters = characters[start_idx:end_idx]
        total_pages = (
            len(characters) + characters_per_page - 1
        ) // characters_per_page

        characters_data = {
            "characters": current_characters,
            "current_page": page + 1,
            "total_pages": total_pages,
            "has_prev": page > 0,
            "has_next": end_idx < len(characters),
            "has_characters": len(characters) > 0,
        }

    return {
        "campaign_name": campaign.title,
        "inviter_name": owner_name,
        "description": campaign.description,
        "campaign_id": campaign_id,
        "characters_data": characters_data,
    }


# === Обработчики кнопок ===
async def on_character_selected(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    item_id: int,
):
    character_id = item_id
    campaign = manager.dialog_data["invite_campaign"]

    logger.info(
        f"Принятие приглашения в кампанию {campaign.title} для персонажа {character_id}"
    )

    try:
        # Принимаем приглашение выбранным персонажем
        result = await api_client.acceptinvite(
            campaign_id=campaign.id, character_id=character_id
        )

        if result.success:
            await callback.answer("✅ Вы успешно присоединились к кампании!")
            await manager.switch_to(states.Menu.main)
        else:
            await callback.answer("❌ Ошибка присоединения к кампании")

    except Exception as e:
        logger.error(f"Ошибка при принятии приглашения: {e}")
        await callback.answer("❌ Произошла ошибка при присоединении")


async def on_page_change(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    direction: int,
):
    current_page = dialog_manager.dialog_data.get("page", 0)
    characters_data = await get_invite_data(dialog_manager)
    total_pages = characters_data["total_pages"]

    new_page = current_page + direction
    if 0 <= new_page < total_pages:
        dialog_manager.dialog_data["page"] = new_page
        await dialog_manager.update({})


async def start_create_character(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    # Сохраняем данные приглашения для возврата
    # manager.dialog_data["invite_data"] = manager.start_data
    await manager.switch_to(states.CrateCharacter.main)


# === Окно приглашения ===
invite_dialog_window = Window(
    Multi(
        Format("🎮 Приглашение в кампанию\n"),
        Format("Кампания: {campaign_name}\n"),
        Format("Пригласил: {inviter_name}\n"),
        Format("Описание: {description}\n\n"),
    ),
    Format(
        "Страница {current_page}/{total_ppages}\n",
        when=lambda data, w, m: data.get("total_pages", 1) > 1,
    ),
    Const("Выберите персонажа для присоединения:\n", when="has_characters"),
    ListGroup(
        Button(
            Format("👤 {item.name} (Ур. {item.level})"),
            id="character",
            on_click=on_character_selected,
        ),
        item_id_getter=lambda item: str(item.id),
        items="characters",
        id="character_group",
        when="has_characters",
    ),
    Const(
        "❌ У вас нет персонажей для присоединения",
        when=lambda data, w, m: not data.get("has_characters", False),
    ),
    Group(
        Row(
            Button(
                Const("⬅️ Назад"),
                id="prev_page",
                on_click=lambda c, b, d: on_page_change(c, b, d, -1),
                when="has_prev",
            ),
            Button(
                Const("Вперед ➡️"),
                id="next_page",
                on_click=lambda c, b, d: on_page_change(c, b, d, 1),
                when="has_next",
            ),
        ),
        width=2,
    ),
    Button(
        Const("➕ Создать нового персонажа"),
        id="create_character",
        on_click=start_create_character,
        when=lambda data, w, m: not data.get("has_characters", False),
    ),
    state=states.Invitation.main,
    getter=get_invite_data,
)

# === Создание диалога и роутера ===
dialog = Dialog(invite_dialog_window)
router = Router()
router.include_router(dialog)
