import logging
from aiogram import Router
from aiogram_dialog import Dialog, Window, DialogManager, SubManager
from aiogram_dialog.widgets.kbd import Button, Group, Row, ListGroup, Cancel, SwitchTo
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram.types import CallbackQuery

from services.api_client import api_client
import states.states as states

logger = logging.getLogger(__name__)


# === Гетеры ===
async def get_characters_data(dialog_manager: DialogManager, **kwargs):
    user_id = dialog_manager.start_data.get("user_id")
    page = dialog_manager.dialog_data.get("page", 0)
    campaigns_per_page = 5

    campaigns = await api_client.get_characters(user_id=user_id)

    if not campaigns:
        return {
            "characters": [],
            "current_page": 1,
            "total_pages": 1,
            "has_prev": False,
            "has_next": False,
            "has_characters": False,
        }

    start_idx = page * campaigns_per_page
    end_idx = start_idx + campaigns_per_page
    current_campaigns = campaigns[start_idx:end_idx]
    total_pages = (len(campaigns) + campaigns_per_page - 1) // campaigns_per_page

    return {
        "characters": current_campaigns,
        "current_page": page + 1,
        "total_pages": total_pages,
        "has_prev": page > 0,
        "has_next": end_idx < len(campaigns),
        "has_characters": len(campaigns) > 0,
    }


# === Кнопки ===
async def on_character_selected(
    callback: CallbackQuery, button: Button, manager: SubManager
):
    await callback.answer("Приходите завтра.")
    return

    character_id = manager.item_id
    logger.info(f"Selected character ID: {character_id}")

    characters_data = await get_characters_data(manager)
    selected_character = next(
        (
            char
            for char in characters_data["characters"]
            if str(char.id) == character_id
        ),
        None,
    )

    if selected_character:
        manager.dialog_data["selected_character"] = selected_character.model_dump()

    await manager.start(
        states.CharacterInfo.main,
        data={"selected_character": selected_character.model_dump()},
    )


async def on_page_change(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    direction: int,
):
    current_page = dialog_manager.dialog_data.get("page", 0)
    campaigns_data = await get_characters_data(dialog_manager)
    total_pages = campaigns_data["total_pages"]

    new_page = current_page + direction
    if 0 <= new_page < total_pages:
        dialog_manager.dialog_data["page"] = new_page
        await dialog_manager.update({})


# === Окна ===
campaign_list_window = Window(
    Multi(
        Const("🏰 Магическая Академия - Ваши персонажи:\n\n"),
        Format(
            "Страница {current_page}/{total_pages}\n",
            when=lambda data, widget, manager: not data.get("total_pages", 1) > 1,
        ),
    ),
    ListGroup(
        Button(
            Format("{item.name}"),
            id="character",
            on_click=on_character_selected,
        ),
        item_id_getter=lambda item: str(item.id),
        items="characters",
        id="character_group",
        when="has_characters",
    ),
    Const(
        "У вас пока нет персонажей",
        when=lambda data, widget, manager: not data.get("has_characters", False),
    ),
    Group(
        Row(
            Button(
                Const("⬅️"),
                id="prev_page",
                on_click=lambda c, b, d: on_page_change(c, b, d, -1),
                when="has_prev",
            ),
            Button(
                Const("➡️"),
                id="next_page",
                on_click=lambda c, b, d: on_page_change(c, b, d, 1),
                when="has_next",
            ),
        ),
        width=2,
    ),
    Cancel(Const("🔙 Назад")),
    SwitchTo(Const("➕ Добавить"), "create_character", states.CrateCharacter.main),
    state=states.CharacterList.main,
    getter=get_characters_data,
)

# === Создание диалога и роутера ===
dialog = Dialog(campaign_list_window)
router = Router()
router.include_router(dialog)
