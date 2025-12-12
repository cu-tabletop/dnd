import json
import logging
from typing import TYPE_CHECKING
from uuid import UUID

from aiogram import Router
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import ManagedTextInput, TextInput
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Cancel,
    Group,
    Row,
    ScrollingGroup,
    Select,
    SwitchTo,
    Url,
)
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, Multi
from tortoise.exceptions import IncompleteInstanceError, IntegrityError, OperationalError

from db.models.campaign import Campaign
from db.models.character import Character
from db.models.participation import Participation
from db.models.user import User
from services.character_data import character_preview_getter
from services.settings import settings
from utils.character import CharacterData as CharData
from utils.character import parse_character_data
from utils.role import Role

from . import states

if TYPE_CHECKING:
    from collections.abc import Sequence

    from db.models.base import CharacterData, UuidModel


logger = logging.getLogger(__name__)


# === Гетеры ===
async def get_character_data(id_: int | UUID) -> User | Character:
    if isinstance(id_, int):
        return await User.get(id=id_)
    return await Character.get(id=id_).prefetch_related("user")


async def get_characters_for_campaign(dialog_manager: DialogManager, **kwargs):
    """Получение персонажей в выбранной кампании"""
    if "campaign_id" not in dialog_manager.dialog_data and isinstance(dialog_manager.start_data, dict):
        dialog_manager.dialog_data["campaign_id"] = dialog_manager.start_data["campaign_id"]

    campaign_id: int = dialog_manager.dialog_data["campaign_id"]
    campaign = await Campaign.get(id=campaign_id)

    list_participation = await Participation.filter(campaign=campaign, role=Role.PLAYER).prefetch_related("user").all()

    if list_participation:
        characters: Sequence[tuple[CharacterData, User, UuidModel]] = [
            (participation.user, participation.user, participation.user) for participation in list_participation
        ]
    else:
        characters: Sequence[tuple[CharacterData, User, UuidModel]] = [
            (char, char.user, char)
            for char in (await Character.filter(campaign=campaign).prefetch_related("user").all())
        ]

    characters_data: list[tuple[CharData, User, UuidModel]] = []
    player_without_characters = []
    for char, user, model_uuid in characters:
        if char.data:
            characters_data.append((parse_character_data(json.loads(char.data["data"])), user, model_uuid))
        else:
            player_without_characters.append(user.username)

    return {
        "characters": characters_data,
        "player_without_characters": " @" + ", @".join(player_without_characters),
        "campaign_title": campaign.title,
        "has_characters": len(characters_data) > 0,
        "is_verified": campaign.verified,
        "has_player_without_characters": len(player_without_characters) > 0,
    }


async def preview_getter(dialog_manager: DialogManager, **kwargs):
    character_id = dialog_manager.dialog_data["character_id"]
    character = await get_character_data(character_id)
    data = json.loads(character.data["data"])

    if isinstance(character, User):
        profile_link = f"https://t.me/{character.username}" if character.username else f"tg://user?id={character.id}"
    else:
        user = character.user
        profile_link = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"

    if isinstance(character, User):
        character_preview = character_preview_getter(character, data)
        return {
            "profile_link": profile_link,
            "user": character,
            "is_verified": True,
            **character_preview,
        }
    user = character.user
    return {
        "profile_link": profile_link,
        "user": user,
        "is_verified": False,
        **character_preview_getter(user, data),
    }


async def get_level(dialog_manager: DialogManager, **kwargs):
    character_id = dialog_manager.dialog_data["character_id"]
    character = await get_character_data(character_id)
    data = character.data or {}

    try:
        json_data = json.loads(data.get("data", "{}"))
        level = json_data.get("info", {}).get("level", {}).get("value", 1)
    except (json.JSONDecodeError, AttributeError):
        level = 1

    return {"level": level}


# === Кнопки (обработчики) ===
async def on_character_selected(
    callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, character_id: str
):
    """Обработчик выбора персонажа"""
    if character_id.isdigit():
        dialog_manager.dialog_data["character_id"] = int(character_id)
    else:
        dialog_manager.dialog_data["character_id"] = UUID(character_id)
    await dialog_manager.next()


async def on_quick_rating_change(callback: CallbackQuery, widget: Button, dialog_manager: DialogManager, change: int):
    """Быстрое изменение рейтинга"""
    try:
        character_id = dialog_manager.dialog_data["character_id"]

        user = await User.get(id=character_id)

        new_rating = user.rating + change

        new_rating = max(new_rating, 0)
        new_rating = min(new_rating, settings.MAX_RATING)

        user.rating = new_rating
        await user.save()

        await dialog_manager.show()

    except (IncompleteInstanceError, IntegrityError, OperationalError) as e:
        logger.exception("Error in quick rating change", exc_info=e)
        await callback.answer("❌ Ошибка при изменении рейтинга", show_alert=True)


async def on_rating_input(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    """Обработчик ввода нового рейтинга"""
    try:
        rating = int(text)
        character_id = dialog_manager.dialog_data["character_id"]

        user = await User.get(id=character_id)

        rating = min(max(0, rating), settings.MAX_RATING)

        user.rating = rating
        await user.save()

        await message.answer(f"✅ Рейтинг успешно изменен на {rating}")
        await dialog_manager.switch_to(states.ManageCharacters.character_menu)

    except ValueError:
        await message.answer("❌ Пожалуйста, введите целое число")
    except (IncompleteInstanceError, IntegrityError, OperationalError) as e:
        logger.exception("Error updating rating", exc_info=e)
        await message.answer("❌ Ошибка при обновлении рейтинга")


async def on_level_input(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    """Обработчик ввода нового уровня"""
    try:
        level = int(text)
        character_id = dialog_manager.dialog_data["character_id"]

        if level < 1:
            await message.answer("❌ Уровень должен быть не меньше 1")
            return
        if level > settings.MAX_LEVEL:
            await message.answer(f"❌ Уровень не может превышать {settings.MAX_LEVEL}")
            return

        character = await get_character_data(character_id)
        character_data = character.data or {}

        character_data["data"] = character_data.get("data", "")

        new_data = json.loads(character_data["data"])
        new_data["info"] = new_data.get("info", {})
        new_data["info"]["level"] = new_data["info"].get("level", {})
        new_data["info"]["level"]["value"] = level

        character_data["data"] = json.dumps(new_data)

        await character.save()
        await message.answer(f"✅ Уровень персонажа изменен на {level}")
        await dialog_manager.switch_to(states.ManageCharacters.character_menu)

    except ValueError:
        await message.answer("❌ Пожалуйста, введите целое число")
    except Exception as e:
        logger.exception("Ошибка при изменении уровня персонажа", exc_info=e)
        await message.answer("❌ Не удалось изменить уровень")


async def on_add_character(mes: CallbackQuery, wif: Button, dialog_manager: DialogManager):
    campaign_id = dialog_manager.dialog_data["campaign_id"]

    await dialog_manager.start(states.InviteMenu.main, data={"campaign_id": campaign_id})


async def on_download_json(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Обработчик скачивания JSON данных персонажа"""
    try:
        character_id = dialog_manager.dialog_data["character_id"]
        character = await get_character_data(character_id)

        data = character.data or {}
        json_str = data.get("data", "{}")

        if isinstance(character, User):
            filename = f"character_{character.username or character.id}.json"
        else:
            filename = f"character_{character.user.username or character.user.id}.json"

        json_bytes = json_str.encode("utf-8")
        input_file = BufferedInputFile(json_bytes, filename=filename)

        if callback.message:
            await callback.message.answer_document(document=input_file)
            await dialog_manager.show()
        else:
            await callback.answer("❌ Ошибка при выгрузке JSON", show_alert=True)

    except Exception as e:
        logger.exception("Error downloading JSON", exc_info=e)
        await callback.answer("❌ Ошибка при выгрузке JSON", show_alert=True)


async def on_view_inventory(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(
        state=states.ManageInventory.view_inventory,
        data={
            "character_id": dialog_manager.dialog_data["character_id"],
            "campaign_id": dialog_manager.dialog_data["campaign_id"],
        },
    )


# === Окна ===
character_selection_window = Window(
    Multi(
        Format("🎭 Выберите персонажа в кампании: {campaign_title}"),
        Const(
            "В этой кампании нет персонажей",
            when=lambda data, *_: not data.get("has_characters", False),
        ),
        Format(
            "Игроки у которых ещё нет персонажей: {player_without_characters}", when="has_player_without_characters"
        ),
        sep="\n",
    ),
    ScrollingGroup(
        Select(
            Format("@{item[1].username} – {item[0].name}"),
            id="character_select",
            items="characters",
            item_id_getter=lambda x: str(x[2].id),
            on_click=on_character_selected,
        ),
        hide_on_single_page=True,
        height=5,
        id="characters_scroll",
    ),
    Button(Const("➕ Добавить"), id="add_character", on_click=on_add_character),
    Cancel(Const("⬅️ Назад")),
    state=states.ManageCharacters.character_selection,
    getter=get_characters_for_campaign,
)

character_detail_window = Window(
    DynamicMedia("avatar", when="avatar"),
    Format("👤 Игрок: @{user.username}"),
    Format("🏆 Текущий рейтинг: {user.rating}", when="is_verified"),
    Format("{character_data_preview}", when="character_data_preview"),
    Url(Const("👤 Перейти в профиль"), Format("{profile_link}")),
    Group(
        SwitchTo(
            Const("📈 Изменить уровень"),
            id="change_level",
            state=states.ManageCharacters.change_level,
            when="character_data_preview",
        ),
        SwitchTo(
            Const("🏆 Изменить рейтинг"),
            id="change_rating",
            state=states.ManageCharacters.quick_rating,
            when="is_verified",
        ),
        Button(
            Const("📥 JSON данные"),
            id="download_json",
            on_click=on_download_json,
        ),
        Button(
            Const("🎒 Управление инвентарем"),
            id="manage_inventory",
            on_click=on_view_inventory,
        ),
        width=2,
    ),
    Back(Const("⬅️ Назад")),
    Cancel(Const("🏠 В главное меню")),
    state=states.ManageCharacters.character_menu,
    getter=preview_getter,
)

change_level_window = Window(
    Const(f"📈 Введите новый уровень персонажа (1-{settings.MAX_LEVEL}):"),
    Format("Сейчас установлен уровень: {level}"),
    TextInput(
        id="level_input",
        on_success=on_level_input,
    ),
    SwitchTo(Const("⬅️ Назад"), id="lvl_to_menu", state=states.ManageCharacters.character_menu),
    getter=get_level,
    state=states.ManageCharacters.change_level,
)

change_rating_window = Window(
    Multi(
        Const("🏆 Изменение рейтинга игрока"),
        Format("Текущий рейтинг: {user.rating}"),
        Const("Введите новый рейтинг:"),
        sep="\n",
    ),
    TextInput(
        id="rating_input",
        on_success=on_rating_input,
    ),
    SwitchTo(Const("⬅️ Назад"), id="rat_to_menu", state=states.ManageCharacters.character_menu),
    state=states.ManageCharacters.change_rating,
    getter=preview_getter,
)

quick_rating_window = Window(
    Multi(
        Const("🏆 Быстрое изменение рейтинга"),
        Format("Игрок: {user.username}"),
        Format("Текущий рейтинг: {user.rating}"),
        Const("Выберите изменение:"),
        sep="\n",
    ),
    Group(
        Row(
            Button(
                Const("+1"),
                id="rating_plus_1",
                on_click=lambda c, b, d: on_quick_rating_change(c, b, d, 1),
            ),
            Button(
                Const("+5"),
                id="rating_plus_5",
                on_click=lambda c, b, d: on_quick_rating_change(c, b, d, 5),
            ),
            Button(
                Const("+10"),
                id="rating_plus_10",
                on_click=lambda c, b, d: on_quick_rating_change(c, b, d, 10),
            ),
        ),
        Row(
            Button(
                Const("-1"),
                id="rating_minus_1",
                on_click=lambda c, b, d: on_quick_rating_change(c, b, d, -1),
            ),
            Button(
                Const("-5"),
                id="rating_minus_5",
                on_click=lambda c, b, d: on_quick_rating_change(c, b, d, -5),
            ),
            Button(
                Const("-10"),
                id="rating_minus_10",
                on_click=lambda c, b, d: on_quick_rating_change(c, b, d, -10),
            ),
        ),
        Button(
            Const("✏️ Ввести точное значение"),
            id="exact_rating",
            on_click=lambda c, b, d: d.switch_to(states.ManageCharacters.change_rating),
        ),
    ),
    SwitchTo(Const("⬅️ Назад"), id="q_rat_to_menu", state=states.ManageCharacters.character_menu),
    state=states.ManageCharacters.quick_rating,
    getter=preview_getter,
)

# === Диалог и роутер ===
dialog = Dialog(
    character_selection_window,
    character_detail_window,
    change_level_window,
    change_rating_window,
    quick_rating_window,
)

router = Router()
router.include_router(dialog)
