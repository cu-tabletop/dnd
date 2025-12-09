import logging
from uuid import UUID

from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import ManagedTextInput, TextInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Group, Row, ScrollingGroup, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format, Multi
from tortoise.exceptions import OperationalError

from db.models.character import Character
from db.models.item import Item
from db.models.user import User
from services.settings import settings

from . import states

logger = logging.getLogger(__name__)


# === Гетеры ===
async def get_character_inventory(dialog_manager: DialogManager, **kwargs):
    """Получение инвентаря персонажа"""
    if "character_id" not in dialog_manager.dialog_data and isinstance(dialog_manager.start_data, dict):
        dialog_manager.dialog_data["campaign_id"] = dialog_manager.start_data["campaign_id"]
        dialog_manager.dialog_data["character_id"] = dialog_manager.start_data["character_id"]

    character_id: int | UUID = dialog_manager.dialog_data["character_id"]
    campaign_id = dialog_manager.dialog_data["campaign_id"]

    if isinstance(character_id, int):
        items = await Item.filter(holder_user=character_id, campaign_id=campaign_id).all()
    else:
        items = await Item.filter(holder_character=character_id, campaign_id=campaign_id).all()

    logger.debug("inventory from %s: %s", character_id, items)

    return {"inventory": items, "has_items": len(items) > 0}


async def get_inventory_item_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных о выбранном предмете"""
    item_id = dialog_manager.dialog_data.get("selected_item_id")
    if not item_id:
        return {"item": None}

    item = await Item.get(id=item_id)
    return {"item": item, "has_description": item.description != ""}


async def get_item_info(dialog_manager: DialogManager, **kwargs):
    return dialog_manager.dialog_data


# === Кнопки (обработчики) ===
async def on_inventory_item_selected(
    callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: UUID
):
    """Обработчик выбора предмета из инвентаря"""
    dialog_manager.dialog_data["selected_item_id"] = item_id
    await dialog_manager.switch_to(states.ManageInventory.edit_inventory_item)


async def on_item_name_input(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    """Обработчик ввода названия предмета"""
    if not text.strip():
        await message.answer("❌ Название не может быть пустым")
        return

    dialog_manager.dialog_data["new_item_name"] = text.strip()
    await dialog_manager.switch_to(states.ManageInventory.add_inventory_item_description)


async def on_item_description_input(
    message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str
):
    """Обработчик ввода описания предмета"""
    description = text.strip() if text.strip() != "-" else ""
    dialog_manager.dialog_data["new_item_description"] = description
    await dialog_manager.switch_to(states.ManageInventory.add_inventory_item_quantity)


async def on_item_quantity_input(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    """Обработчик ввода количества предмета"""
    try:
        quantity = int(text) if text.strip() else 1
        if quantity <= 0:
            await message.answer("❌ Количество должно быть положительным числом")
            return
        if quantity > settings.MAX_ITEM_QUANTITY:
            await message.answer(f"❌ Количество не может превышать {settings.MAX_ITEM_QUANTITY}")
            return
    except ValueError:
        await message.answer("❌ Пожалуйста, введите целое число")
        return

    # Создаем и сохраняем предмет
    character_id = dialog_manager.dialog_data.get("character_id")
    campaign_id = dialog_manager.dialog_data.get("campaign_id")

    try:
        holder: dict[str, User | Character]
        if isinstance(character_id, int):
            holder = {"holder_user": await User.get(id=character_id)}
        else:
            holder = {"holder_character": await Character.get(id=character_id)}

        item = await Item.create(
            title=dialog_manager.dialog_data["new_item_name"],
            description=dialog_manager.dialog_data.get("new_item_description", ""),
            quantity=quantity,
            campaign_id=campaign_id,
            **holder,  # type: ignore  # noqa: PGH003
        )

        await message.answer(f"✅ Предмет '{item.title}' успешно добавлен!")
        await dialog_manager.switch_to(states.ManageInventory.view_inventory)

    except Exception as e:
        logger.exception("Error adding inventory item", exc_info=e)
        await message.answer("❌ Ошибка при добавлении предмета")


async def on_edit_item_name(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    """Обработчик изменения названия предмета"""
    if not text.strip():
        await message.answer("❌ Название не может быть пустым")
        return

    item_id = dialog_manager.dialog_data.get("selected_item_id")

    try:
        item = await Item.get(id=item_id)
        item.title = text.strip()
        await item.save()

        await message.answer(f"✅ Название изменено на: {text.strip()}")
        await dialog_manager.switch_to(states.ManageInventory.view_inventory)

    except Exception as e:
        logger.exception("Error updating item name: e", exc_info=e)
        await message.answer("❌ Ошибка при изменении названия")


async def on_edit_item_description(
    message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str
):
    """Обработчик изменения описания предмета"""
    description = text.strip() if text.strip() != "-" else ""
    item_id = dialog_manager.dialog_data.get("selected_item_id")

    try:
        item = await Item.get(id=item_id)
        item.description = description
        await item.save()

        await message.answer("✅ Описание изменено")
        await dialog_manager.switch_to(states.ManageInventory.view_inventory)

    except Exception as e:
        logger.exception("Error updating item description: ", exc_info=e)
        await message.answer("❌ Ошибка при изменении описания")


async def on_edit_item_quantity(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    """Обработчик изменения количества предмета"""
    try:
        quantity = int(text)
        if quantity <= 0:
            await message.answer("❌ Количество должно быть положительным числом")
            return
        if quantity > MAX_QUANTITY_ITEM:
            await message.answer("❌ Количество не может превышать 1000")
            return
    except ValueError:
        await message.answer("❌ Пожалуйста, введите целое число")
        return

    item_id = dialog_manager.dialog_data.get("selected_item_id")

    try:
        item = await Item.get(id=item_id)
        item.quantity = quantity
        await item.save()

        await message.answer(f"✅ Количество изменено на: {quantity}")
        await dialog_manager.switch_to(states.ManageInventory.view_inventory)

    except Exception as e:
        logger.exception("Error updating item quantity", exc_info=e)
        await message.answer("❌ Ошибка при изменении количества")


async def on_delete_inventory_item(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Обработчик удаления предмета"""
    item_id = dialog_manager.dialog_data["selected_item_id"]

    try:
        item = await Item.get(id=item_id)
        item_title = item.title
        await item.delete()

        await callback.answer(f"✅ Предмет '{item_title}' удален", show_alert=True)
        await dialog_manager.switch_to(states.ManageInventory.view_inventory)

    except OperationalError as e:
        logger.exception("Error deleting inventory item", exc_info=e)
        await callback.answer("❌ Ошибка при удалении предмета", show_alert=True)


# === Окна ===
view_inventory_window = Window(
    Multi(
        Const("🎒 Инвентарь персонажа"),
        Const(""),
        Const("Выберите предмет для редактирования:"),
        Const("В инвентаре пока нет предметов", when=lambda data, *_: not data.get("has_items", False)),
        sep="\n",
    ),
    ScrollingGroup(
        Select(
            Format("{item.title} ×{item.quantity}"),
            id="inventory_select",
            item_id_getter=lambda item: item.id,
            items="inventory",
            on_click=on_inventory_item_selected,
            type_factory=UUID,
        ),
        id="inventory_scroll",
        width=1,
        height=10,
        hide_on_single_page=True,
        when="has_items",
    ),
    Row(
        SwitchTo(
            Const("➕ Добавить предмет"),
            id="add_item",
            state=states.ManageInventory.add_inventory_item,
        ),
        Cancel(Const("⬅️ Назад")),
    ),
    state=states.ManageInventory.view_inventory,
    getter=get_character_inventory,
)

add_inventory_item_window = Window(
    Const("➕ Добавление нового предмета\n\nВведите название предмета:"),
    TextInput(
        id="item_name_input",
        on_success=on_item_name_input,
    ),
    SwitchTo(Const("❌ Отмена"), id="cns_inv", state=states.ManageInventory.view_inventory),
    state=states.ManageInventory.add_inventory_item,
)

add_item_description_window = Window(
    Format("Название {new_item_name}"),
    Const("📝 Введите описание предмета (или '-' чтобы пропустить):"),
    TextInput(
        id="item_description_input",
        on_success=on_item_description_input,
    ),
    SwitchTo(Const("❌ Отмена"), id="cns_inv", state=states.ManageInventory.view_inventory),
    state=states.ManageInventory.add_inventory_item_description,
    getter=get_item_info,
)

add_item_quantity_window = Window(
    Format("Название: {new_item_name}"),
    Format("Описание {new_item_description}"),
    Const("🔢 Введите количество предмета:"),
    TextInput(
        id="item_quantity_input",
        on_success=on_item_quantity_input,
    ),
    SwitchTo(Const("❌ Отмена"), id="cns_inv", state=states.ManageInventory.view_inventory),
    getter=get_item_info,
    state=states.ManageInventory.add_inventory_item_quantity,
)

edit_inventory_item_window = Window(
    Multi(
        Const("✏️ Редактирование предмета"),
        Format("📦 {item.title}"),
        Format("📝 Описание: {item.description}", when="has_description"),
        Const("📝 Описание отсутствует", when=lambda data, *_: not data.get("item", {}).description),
        Format("🔢 Количество: {item.quantity}"),
        Const(""),
        Const("Выберите что изменить:"),
        sep="\n",
    ),
    Group(
        SwitchTo(
            Const("✏️ Название"),
            id="edit_name",
            state=states.ManageInventory.edit_inventory_item_name,
        ),
        SwitchTo(
            Const("📝 Описание"),
            id="edit_description",
            state=states.ManageInventory.edit_inventory_item_description,
        ),
        SwitchTo(
            Const("🔢 Количество"),
            id="edit_quantity",
            state=states.ManageInventory.edit_inventory_item_quantity,
        ),
        SwitchTo(
            Const("🗑️ Удалить"),
            id="delete_item",
            state=states.ManageInventory.accept_delete,
        ),
    ),
    SwitchTo(Const("⬅️ Назад"), id="cns_inv", state=states.ManageInventory.view_inventory),
    state=states.ManageInventory.edit_inventory_item,
    getter=get_inventory_item_data,
)

edit_item_name_window = Window(
    Format("📦 Текущие название: {item.title}"),
    Const("✏️ Введите новое название предмета:"),
    TextInput(
        id="edit_name_input",
        on_success=on_edit_item_name,
    ),
    SwitchTo(Const("⬅️ Назад"), id="ens_inv", state=states.ManageInventory.edit_inventory_item),
    getter=get_inventory_item_data,
    state=states.ManageInventory.edit_inventory_item_name,
)

edit_item_description_window = Window(
    Format("📜 Текущие описание: {item.description}", when="has_description"),
    Const("📝 Введите новое описание предмета (или '-' чтобы очистить):"),
    TextInput(
        id="edit_description_input",
        on_success=on_edit_item_description,
    ),
    SwitchTo(Const("⬅️ Назад"), id="ens_inv", state=states.ManageInventory.edit_inventory_item),
    getter=get_inventory_item_data,
    state=states.ManageInventory.edit_inventory_item_description,
)

edit_item_quantity_window = Window(
    Format("ℹ️ Текущее количество: {item.quantity}"),
    Const("🔢 Введите новое количество предмета:"),
    TextInput(
        id="edit_quantity_input",
        on_success=on_edit_item_quantity,
    ),
    getter=get_inventory_item_data,
    state=states.ManageInventory.edit_inventory_item_quantity,
)

accept_delete_item_window = Window(
    Const("🎯 Точно удалить?"),
    Button(
        Const("🚫 Удалить"),
        id="accept_delete",
        on_click=on_delete_inventory_item,
    ),
    SwitchTo(Const("⬅️ Назад"), id="ens_inv", state=states.ManageInventory.edit_inventory_item),
    state=states.ManageInventory.accept_delete,
)

# === Диалог и роутер ===
dialog = Dialog(
    view_inventory_window,
    add_inventory_item_window,
    add_item_description_window,
    add_item_quantity_window,
    edit_inventory_item_window,
    edit_item_name_window,
    edit_item_description_window,
    edit_item_quantity_window,
    accept_delete_item_window,
)

router = Router()
router.include_router(dialog)
