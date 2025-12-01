import logging
from aiogram import Router
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import (
    Button,
    Row,
    Group,
    Back,
    Cancel,
    Select,
    ScrollingGroup,
)
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput
from aiogram.types import Message, CallbackQuery

from services.api_client import api_client
from services.models import InventoryItemCreate, InventoryItemUpdate
from . import states as campaign_states

logger = logging.getLogger(__name__)

# ========== ГЕТТЕРЫ ==========


async def get_character_inventory(dialog_manager: DialogManager, **kwargs):
    """Получение инвентаря персонажа"""
    character_id = dialog_manager.start_data.get("character_id")
    dialog_manager.dialog_data["character_id"] = character_id
    inventory = await api_client.get_character_inventory(character_id)
    logger.info(
        f"Получение инвентаря для персонажа {character_id}: {inventory}"
    )
    return {"inventory": inventory, "character_id": character_id}


async def get_inventory_item_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных о выбранном предмете"""
    item_id = dialog_manager.dialog_data.get("selected_item_id")
    character_id = dialog_manager.dialog_data.get("character_id")

    inventory = await api_client.get_character_inventory(character_id)
    logger.debug(
        f"Получены: предмет – {item_id}, инвентарь – {inventory} от {character_id}"
    )
    item = next((i for i in inventory if i.id == item_id), None)

    return {"item": item, "character_id": character_id}


# ========== ОБРАБОТЧИКИ ПРОСМОТРА ИНВЕНТАРЯ ==========


async def on_inventory_item_selected(
    callback: CallbackQuery,
    widget: Select,
    manager: DialogManager,
    item_id: str,
):
    """Обработчик выбора предмета из инвентаря"""
    manager.dialog_data["selected_item_id"] = int(item_id)
    await manager.switch_to(
        campaign_states.ManageInventory.edit_inventory_item
    )


# ========== ОБРАБОТЧИКИ ДОБАВЛЕНИЯ ПРЕДМЕТА ==========


async def on_add_inventory_item(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    """Обработчик добавления предмета"""
    await manager.switch_to(campaign_states.ManageInventory.add_inventory_item)


async def on_item_name_input(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    text: str,
):
    """Обработчик ввода названия предмета"""
    if not text.strip():
        await message.answer("❌ Название не может быть пустым")
        return

    manager.dialog_data["new_item_name"] = text.strip()
    await message.answer(
        f"✅ Название: {text.strip()}\nТеперь введите описание (или отправьте '-' "
        f"чтобы пропустить):"
    )
    await manager.switch_to(
        campaign_states.ManageInventory.add_inventory_item_description
    )


async def on_item_description_input(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    text: str,
):
    """Обработчик ввода описания предмета"""
    description = text.strip() if text.strip() != "-" else ""
    manager.dialog_data["new_item_description"] = description
    await message.answer(
        f"📝 Описание: {description if description else 'не указано'}\nТеперь введите "
        "количество (или отправьте '1' по умолчанию):"
    )
    await manager.switch_to(
        campaign_states.ManageInventory.add_inventory_item_quantity
    )


async def on_item_quantity_input(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    text: str,
):
    """Обработчик ввода количества предмета"""
    try:
        quantity = int(text) if text.strip() else 1
        if quantity <= 0:
            await message.answer(
                "❌ Количество должно быть положительным числом"
            )
            return
        if quantity > 1000:
            await message.answer("❌ Количество не может превышать 1000")
            return
    except ValueError:
        await message.answer("❌ Пожалуйста, введите целое число")
        return

    # Создаем и сохраняем предмет
    character_id = manager.dialog_data.get("character_id")
    new_item = InventoryItemCreate(
        name=manager.dialog_data["new_item_name"],
        description=manager.dialog_data.get("new_item_description", ""),
        quantity=quantity,
    )

    try:
        result = await api_client.add_inventory_item(character_id, new_item)
        if hasattr(result, "error"):
            await message.answer(f"❌ Ошибка: {result.error}")
        else:
            await message.answer(
                f"✅ Предмет '{result.name}' успешно добавлен!"
            )
        await manager.switch_to(campaign_states.ManageInventory.view_inventory)
    except Exception as e:
        logger.error(f"Error adding inventory item: {e}")
        await message.answer("❌ Ошибка при добавлении предмета")
        await manager.switch_to(campaign_states.ManageInventory.view_inventory)


# ========== ОБРАБОТЧИКИ РЕДАКТИРОВАНИЯ ПРЕДМЕТА ==========


async def on_edit_item_name(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    text: str,
):
    """Обработчик изменения названия предмета"""
    if not text.strip():
        await message.answer("❌ Название не может быть пустым")
        return

    item_id = manager.dialog_data.get("selected_item_id")
    update_data = InventoryItemUpdate(name=text.strip())

    try:
        result = await api_client.update_inventory_item(item_id, update_data)
        if hasattr(result, "error"):
            await message.answer(f"❌ Ошибка: {result.error}")
        else:
            await message.answer(f"✅ Название изменено на: {text.strip()}")
        await manager.switch_to(campaign_states.ManageInventory.view_inventory)
    except Exception as e:
        logger.error(f"Error updating item name: {e}")
        await message.answer("❌ Ошибка при изменении названия")
        await manager.switch_to(campaign_states.ManageInventory.view_inventory)


async def on_edit_item_description(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    text: str,
):
    """Обработчик изменения описания предмета"""
    description = text.strip() if text.strip() != "-" else ""
    item_id = manager.dialog_data.get("selected_item_id")
    update_data = InventoryItemUpdate(description=description)

    try:
        result = await api_client.update_inventory_item(item_id, update_data)
        if hasattr(result, "error"):
            await message.answer(f"❌ Ошибка: {result.error}")
        else:
            await message.answer("✅ Описание изменено")
        await manager.switch_to(campaign_states.ManageInventory.view_inventory)
    except Exception as e:
        logger.error(f"Error updating item description: {e}")
        await message.answer("❌ Ошибка при изменении описания")
        await manager.switch_to(campaign_states.ManageInventory.view_inventory)


async def on_edit_item_quantity(
    message: Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    text: str,
):
    """Обработчик изменения количества предмета"""
    try:
        quantity = int(text)
        if quantity <= 0:
            await message.answer(
                "❌ Количество должно быть положительным числом"
            )
            return
        if quantity > 1000:
            await message.answer("❌ Количество не может превышать 1000")
            return
    except ValueError:
        await message.answer("❌ Пожалуйста, введите целое число")
        return

    item_id = manager.dialog_data.get("selected_item_id")
    update_data = InventoryItemUpdate(quantity=quantity)

    try:
        result = await api_client.update_inventory_item(item_id, update_data)
        if hasattr(result, "error"):
            await message.answer(f"❌ Ошибка: {result.error}")
        else:
            await message.answer(f"✅ Количество изменено на: {quantity}")
        await manager.switch_to(campaign_states.ManageInventory.view_inventory)
    except Exception as e:
        logger.error(f"Error updating item quantity: {e}")
        await message.answer("❌ Ошибка при изменении количества")
        await manager.switch_to(campaign_states.ManageInventory.view_inventory)


async def on_delete_inventory_item(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    """Обработчик удаления предмета"""
    item_id = manager.dialog_data.get("selected_item_id")

    try:
        result = await api_client.delete_inventory_item(item_id)
        if hasattr(result, "error"):
            await callback.answer(
                f"❌ Ошибка: {result.error}", show_alert=True
            )
        else:
            await callback.answer("✅ Предмет удален", show_alert=True)
        await manager.switch_to(campaign_states.ManageInventory.view_inventory)
    except Exception as e:
        logger.error(f"Error deleting inventory item: {e}")
        await callback.answer(
            "❌ Ошибка при удалении предмета", show_alert=True
        )
        await manager.switch_to(campaign_states.ManageInventory.view_inventory)


# ========== ОКНА ДИАЛОГА ==========

# Окно просмотра инвентаря
view_inventory_window = Window(
    Multi(
        Format("🎒 Инвентарь персонажа"),
        Const(""),
        Const("Выберите предмет для редактирования:"),
        sep="\n",
    ),
    ScrollingGroup(
        Select(
            Format("{item.name} ×{item.quantity}"),
            id="s_inventory",
            item_id_getter=lambda item: str(item.id),
            items="inventory",
            on_click=on_inventory_item_selected,
        ),
        id="inventory_scroll",
        width=1,
        height=10,
    ),
    Row(
        Button(
            Const("➕ Добавить предмет"),
            id="add_item",
            on_click=on_add_inventory_item,
        ),
        Cancel(Const("⬅️ Назад")),
    ),
    state=campaign_states.ManageInventory.view_inventory,
    getter=get_character_inventory,
)

# Окно добавления предмета
add_inventory_item_window = Window(
    Const("➕ Добавление нового предмета\n\nВведите название предмета:"),
    TextInput(
        id="item_name_input",
        on_success=on_item_name_input,
    ),
    Back(Const("⬅️ Назад")),
    state=campaign_states.ManageInventory.add_inventory_item,
)

# Окно ввода описания предмета
add_item_description_window = Window(
    Const("📝 Введите описание предмета (или '-' чтобы пропустить):"),
    TextInput(
        id="item_description_input",
        on_success=on_item_description_input,
    ),
    Back(Const("⬅️ Назад")),
    state=campaign_states.ManageInventory.add_inventory_item_description,
)

# Окно ввода количества предмета
add_item_quantity_window = Window(
    Const("🔢 Введите количество предмета:"),
    TextInput(
        id="item_quantity_input",
        on_success=on_item_quantity_input,
    ),
    Back(Const("⬅️ Назад")),
    state=campaign_states.ManageInventory.add_inventory_item_quantity,
)

# Окно редактирования предмета
edit_inventory_item_window = Window(
    Multi(
        Format("✏️ Редактирование предмета"),
        Format("📦 {item.name}"),
        Format("📝 {item.description}"),
        Format("🔢 Количество: {item.quantity}"),
        Const(""),
        Const("Выберите что изменить:"),
        sep="\n",
    ),
    Group(
        Button(
            Const("✏️ Название"),
            id="edit_name",
            on_click=lambda c, b, m: m.switch_to(
                campaign_states.ManageInventory.edit_inventory_item_name
            ),
        ),
        Button(
            Const("📝 Описание"),
            id="edit_description",
            on_click=lambda c, b, m: m.switch_to(
                campaign_states.ManageInventory.edit_inventory_item_description
            ),
        ),
        Button(
            Const("🔢 Количество"),
            id="edit_quantity",
            on_click=lambda c, b, m: m.switch_to(
                campaign_states.ManageInventory.edit_inventory_item_quantity
            ),
        ),
        Button(
            Const("🗑️ Удалить"),
            id="delete_item",
            on_click=on_delete_inventory_item,
        ),
    ),
    Back(Const("⬅️ Назад")),
    state=campaign_states.ManageInventory.edit_inventory_item,
    getter=get_inventory_item_data,
)

# Окна редактирования отдельных полей
edit_item_name_window = Window(
    Const("✏️ Введите новое название предмета:"),
    TextInput(
        id="edit_name_input",
        on_success=on_edit_item_name,
    ),
    Back(Const("⬅️ Назад")),
    state=campaign_states.ManageInventory.edit_inventory_item_name,
)

edit_item_description_window = Window(
    Const("📝 Введите новое описание предмета (или '-' чтобы очистить):"),
    TextInput(
        id="edit_description_input",
        on_success=on_edit_item_description,
    ),
    Back(Const("⬅️ Назад")),
    state=campaign_states.ManageInventory.edit_inventory_item_description,
)

edit_item_quantity_window = Window(
    Const("🔢 Введите новое количество предмета:"),
    TextInput(
        id="edit_quantity_input",
        on_success=on_edit_item_quantity,
    ),
    Back(Const("⬅️ Назад")),
    state=campaign_states.ManageInventory.edit_inventory_item_quantity,
)

# Создаем диалог управления инвентарем
inventory_management_dialog = Dialog(
    view_inventory_window,
    add_inventory_item_window,
    add_item_description_window,
    add_item_quantity_window,
    edit_inventory_item_window,
    edit_item_name_window,
    edit_item_description_window,
    edit_item_quantity_window,
)

router = Router()
router.include_router(inventory_management_dialog)
