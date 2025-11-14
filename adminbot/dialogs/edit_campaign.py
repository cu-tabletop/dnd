from aiogram import Router
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Group, Cancel, SwitchTo, Column
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput
from aiogram.types import CallbackQuery, Message

from . import states as campaign_states


# === Гетеры ===
async def get_campaign_edit_data(dialog_manager: DialogManager, **kwargs):
    campaign = dialog_manager.start_data.get("selected_campaign", {})  # type: ignore
    dialog_manager.dialog_data["selected_campaign"] = campaign
    return {
        "campaign_title": campaign.get("title", "Неизвестная группа"),
        "campaign_description": campaign.get(
            "description", "Описание отсутствует"
        ),
        "campaign_icon": campaign.get("icon", "🏰"),
        "campaign_id": campaign.get("id", "N/A"),
    }


# === Кнопки ===
async def on_field_selected(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    field_map = {
        "title": campaign_states.EditCampaignInfo.edit_title,
        "description": campaign_states.EditCampaignInfo.edit_description,
        "icon": campaign_states.EditCampaignInfo.edit_icon,
    }
    if button.widget_id in field_map:
        await dialog_manager.switch_to(field_map[button.widget_id])


async def on_title_edited(
    message: Message,
    widget: TextInput,
    dialog_manager: DialogManager,
    text: str,
):
    if len(text) > 255:
        await message.answer(
            "Название слишком длинное (максимум 255 символов)"
        )
        return

    if "selected_campaign" not in dialog_manager.dialog_data:
        dialog_manager.dialog_data["selected_campaign"] = {}
    dialog_manager.dialog_data["selected_campaign"]["title"] = text

    await dialog_manager.switch_to(campaign_states.EditCampaignInfo.confirm)


async def on_description_edited(
    message: Message,
    widget: TextInput,
    dialog_manager: DialogManager,
    text: str,
):
    if len(text) > 1023:
        await message.answer(
            "Описание слишком длинное (максимум 1023 символа)"
        )
        return

    if "selected_campaign" not in dialog_manager.dialog_data:
        dialog_manager.dialog_data["selected_campaign"] = {}
    dialog_manager.dialog_data["selected_campaign"]["description"] = text

    await dialog_manager.switch_to(campaign_states.EditCampaignInfo.confirm)


async def on_icon_selected_edit(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    icon_map = {
        "castle_edit": "🏰",
        "books_edit": "📚",
        "lightning_edit": "⚡",
        "fire_edit": "🔥",
        "moon_edit": "🌙",
        "star_edit": "⭐",
    }
    icon = icon_map.get(button.widget_id, "🏰")  # type: ignore

    if "selected_campaign" not in dialog_manager.dialog_data:
        dialog_manager.dialog_data["selected_campaign"] = {}
    dialog_manager.dialog_data["selected_campaign"]["icon"] = icon

    await dialog_manager.switch_to(campaign_states.EditCampaignInfo.confirm)


async def on_edit_confirm(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    campaign = dialog_manager.dialog_data.get("selected_campaign", {})
    await callback.answer(  # type: ignore
        f"✅ Изменения для {campaign.get('title')} сохранены!", show_alert=True
    )
    await dialog_manager.back()


# === Окна ===
select_field_window = Window(
    Format(
        "✏️ Редактирование группы: {campaign_icon} {campaign_title}\n\n"
        "Выберите что хотите изменить:"
    ),
    Column(
        Button(
            Const("📝 Название группы"), id="title", on_click=on_field_selected
        ),
        Button(
            Const("📄 Описание группы"),
            id="description",
            on_click=on_field_selected,
        ),
        Button(
            Const("🎨 Иконка группы"), id="icon", on_click=on_field_selected
        ),
    ),
    Cancel(Const("⬅️ Назад")),
    state=campaign_states.EditCampaignInfo.select_field,
    getter=get_campaign_edit_data,
)

edit_title_window = Window(
    Const("Введите новое название группы:"),
    TextInput(id="edit_title_input", on_success=on_title_edited),  # type: ignore
    SwitchTo(
        Const("⬅️ Назад"),
        id="back_from_title",
        state=campaign_states.EditCampaignInfo.select_field,
    ),
    state=campaign_states.EditCampaignInfo.edit_title,
)

edit_description_window = Window(
    Const("Введите новое описание группы:"),
    TextInput(
        id="edit_description_input",
        on_success=on_description_edited,  # type: ignore
    ),
    SwitchTo(
        Const("⬅️ Назад"),
        id="back_from_description",
        state=campaign_states.EditCampaignInfo.select_field,
    ),
    state=campaign_states.EditCampaignInfo.edit_description,
)

edit_icon_window = Window(
    Const("Выберите новую иконку для группы:"),
    Group(
        Button(
            Const("🏰 Замок"), id="castle_edit", on_click=on_icon_selected_edit
        ),
        Button(
            Const("📚 Книги"), id="books_edit", on_click=on_icon_selected_edit
        ),
        Button(
            Const("⚡ Молния"),
            id="lightning_edit",
            on_click=on_icon_selected_edit,
        ),
        Button(
            Const("🔥 Огонь"), id="fire_edit", on_click=on_icon_selected_edit
        ),
        Button(
            Const("🌙 Луна"), id="moon_edit", on_click=on_icon_selected_edit
        ),
        Button(
            Const("⭐ Звезда"), id="star_edit", on_click=on_icon_selected_edit
        ),
        width=2,
    ),
    SwitchTo(
        Const("⬅️ Назад"),
        id="back_from_icon",
        state=campaign_states.EditCampaignInfo.select_field,
    ),
    state=campaign_states.EditCampaignInfo.edit_icon,
)

confirm_edit_window = Window(
    Format(
        "✅ Проверьте изменения:\n\n"
        "🎨 Иконка: {campaign_icon}\n"
        "📝 Название: {campaign_title}\n"
        "📄 Описание: {campaign_description}\n\n"
        "Сохранить изменения?"
    ),
    Button(Const("✅ Сохранить"), id="save_changes", on_click=on_edit_confirm),
    SwitchTo(
        Const("⬅️ Назад"),
        id="back_from_confirm",
        state=campaign_states.EditCampaignInfo.select_field,
    ),
    Cancel(Const("❌ Отмена")),
    state=campaign_states.EditCampaignInfo.confirm,
    getter=get_campaign_edit_data,
)

# === Создание диалога и роутера ===
dialog = Dialog(
    select_field_window,
    edit_title_window,
    edit_description_window,
    edit_icon_window,
    confirm_edit_window,
)
router = Router()
router.include_router(dialog)
