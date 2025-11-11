import logging
from aiogram import Router
from aiogram.types.input_file import BufferedInputFile
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import (
    Button,
    Row,
    Back,
    Select,
    ScrollingGroup,
)
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput
from aiogram.types import Message, CallbackQuery

# from aiogram_dialog.api.entities import ShowMode

from services.api_client import get_api_client

# from models.models import (
#     CharacterShort,
#     CharacterDetail,
#     InventoryItemCreate,
#     InventoryItemUpdate,
# )
from .states import CharacterManagerSG

api_client = get_api_client()
logger = logging.getLogger(__name__)

# ========== ГЕТТЕРЫ ==========


async def get_company_characters(dialog_manager: DialogManager, **kwargs):
    """Получение персонажей компании"""
    company_id = dialog_manager.dialog_data.get("company_id")
    characters = await api_client.get_company_characters_short(
        company_id  # type: ignore
    )
    return {
        "characters": characters,
        "has_characters": len(characters) > 0,
        "company_id": company_id,
    }


async def get_character_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных о выбранном персонаже"""
    character_id = dialog_manager.dialog_data.get("character_id")
    character = await api_client.get_character(character_id)  # type: ignore
    return {"character": character}


# ========== ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ ==========


async def on_character_selected(
    callback: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    """Обработчик выбора персонажа"""
    character_id = int(item_id)
    manager.dialog_data["character_id"] = character_id

    # Сохраняем информацию о персонаже
    characters = await get_company_characters(manager)
    selected_character = next(
        (c for c in characters["characters"] if c.id == character_id), None
    )
    if selected_character:
        manager.dialog_data["character_name"] = selected_character.name

    await manager.switch_to(CharacterManagerSG.character_selected)


# ========== ОБРАБОТЧИКИ РЕДАКТИРОВАНИЯ ПЕРСОНАЖА ==========
# (Переносим существующие обработчики из character_management.py)


async def on_change_level(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(CharacterManagerSG.change_level)


async def on_change_rating(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(CharacterManagerSG.change_rating)


async def on_view_inventory(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(CharacterManagerSG.view_inventory)


async def on_download_jpeg(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    character_id = manager.dialog_data.get("character_id")
    try:
        jpeg_data = await api_client.get_character_jpeg(character_id)  # type: ignore
        await callback.message.answer_document(  # type: ignore
            document=BufferedInputFile(
                jpeg_data, filename=f"character_{character_id}.jpg"
            )
        )
    except Exception:
        await callback.message.answer("❌ Ошибка при загрузке файла")  # type: ignore


async def on_level_input(
    message: Message, widget: ManagedTextInput, manager: DialogManager, text: str
):
    try:
        level = int(text)
        character_id = manager.dialog_data.get("character_id")
        await api_client.update_character_level(character_id, level)  # type: ignore
        await message.answer(f"✅ Уровень изменен на {level}")
        await manager.switch_to(CharacterManagerSG.character_selected)
    except ValueError:
        await message.answer("❌ Введите целое число")
    except Exception as e:
        logger.error(f"Error updating level: {e}")
        await message.answer("❌ Ошибка при обновлении уровня")


async def on_rating_input(
    message: Message, widget: ManagedTextInput, manager: DialogManager, text: str
):
    try:
        rating = int(text)
        character_id = manager.dialog_data.get("character_id")
        await api_client.update_character_rating(character_id, rating)  # type: ignore
        await message.answer(f"✅ Рейтинг изменен на {rating}")
        await manager.switch_to(CharacterManagerSG.character_selected)
    except ValueError:
        await message.answer("❌ Введите целое число")
    except Exception as e:
        logger.error(f"Error updating rating: {e}")
        await message.answer("❌ Ошибка при обновлении рейтинга")


# ========== ОКНА ДИАЛОГА ==========

# Главное окно менеджера персонажей
main_window = Window(
    Multi(
        Format("🧙 Менеджер персонажей"),
        Const(""),
        Const("Персонажи компании:"),
        Const(
            "📝 В этой компании пока нет персонажей.",
            when=lambda data, *args, **kwargs: not data["has_characters"],
        ),
        sep="\n",
    ),
    ScrollingGroup(
        Select(
            Format("👤 {item.name} (Ур. {item.level}) - {item.player_tg_username}"),
            id="s_characters",
            item_id_getter=lambda item: item.id,
            items="characters",
            on_click=on_character_selected,
        ),
        id="characters_scroll",
        width=1,
        height=8,
        when="has_characters",
    ),
    Back(Const("⬅️ Назад")),
    state=CharacterManagerSG.main,
    getter=get_company_characters,
)

# Окно выбранного персонажа
character_selected_window = Window(
    Multi(
        Format("🧙 Персонаж: {character.name}"),
        Format("👤 Игрок: {character.player_tg_username}"),
        Format("⭐ Уровень: {character.level}"),
        Format("🏆 Рейтинг: {character.rating}"),
        sep="\n",
    ),
    Row(
        Button(Const("📈 Уровень"), id="change_level", on_click=on_change_level),
        Button(Const("🏆 Рейтинг"), id="change_rating", on_click=on_change_rating),
    ),
    Row(
        Button(Const("🎒 Инвентарь"), id="view_inventory", on_click=on_view_inventory),
        Button(Const("📥 Скачать JPEG"), id="download_jpeg", on_click=on_download_jpeg),
    ),
    Back(Const("⬅️ К списку персонажей")),
    state=CharacterManagerSG.character_selected,
    getter=get_character_data,
)

# Окна редактирования (переносим из character_management.py)
level_window = Window(
    Const("Введите новый уровень персонажа:"),
    TextInput(id="level_input", on_success=on_level_input),
    Back(Const("⬅️ Назад")),
    state=CharacterManagerSG.change_level,
)

rating_window = Window(
    Const("Введите новый рейтинг персонажа:"),
    TextInput(id="rating_input", on_success=on_rating_input),
    Back(Const("⬅️ Назад")),
    state=CharacterManagerSG.change_rating,
)

# Создаем диалог (инвентарь добавим отдельно)
character_manager_dialog = Dialog(
    main_window,
    character_selected_window,
    level_window,
    rating_window,
    # Добавим окна инвентаря позже
)

router = Router()
router.include_router(character_manager_dialog)
