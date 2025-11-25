from aiogram import Router
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Group, Cancel, SwitchTo, Column
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram_dialog.widgets.input import TextInput
from aiogram.types import CallbackQuery, Message

from services.models import CampaignModelSchema
from . import states as campaign_states


# === Гетеры ===
async def get_campaign_edit_data(dialog_manager: DialogManager, **kwargs):
    campaign_data = dialog_manager.start_data.get("selected_campaign", {})
    campaign = CampaignModelSchema(**campaign_data)
    dialog_manager.dialog_data["selected_campaign"] = campaign_data

    # Готовим текст статуса иконки заранее
    icon_status = "🖼 установлена" if campaign.icon else "❌ не установлена"

    return {
        "campaign_title": campaign.title,
        "campaign_description": campaign.description or "Описание отсутствует",
        "icon_status": icon_status,
        "campaign_id": campaign.id or "N/A",
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
        await message.answer("Название слишком длинное (максимум 255 символов)")
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
        await message.answer("Описание слишком длинное (максимум 1023 символа)")
        return

    if "selected_campaign" not in dialog_manager.dialog_data:
        dialog_manager.dialog_data["selected_campaign"] = {}
    dialog_manager.dialog_data["selected_campaign"]["description"] = text

    await dialog_manager.switch_to(campaign_states.EditCampaignInfo.confirm)


async def on_edit_confirm(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    campaign_data = dialog_manager.dialog_data.get("selected_campaign", {})
    campaign = CampaignModelSchema(**campaign_data)
    await callback.answer(
        f"✅ Изменения для {campaign.title} сохранены!", show_alert=True
    )
    await dialog_manager.back()


# === Окна ===
select_field_window = Window(
    Multi(
        Format("✏️ Редактирование группы: {campaign_title}\n\n"),
        Format("Иконка: {icon_status}\n\n"),
        Const("Выберите что хотите изменить:"),
    ),
    Column(
        Button(Const("📝 Название группы"), id="title", on_click=on_field_selected),
        Button(
            Const("📄 Описание группы"),
            id="description",
            on_click=on_field_selected,
        ),
        Button(Const("🎨 Иконка группы"), id="icon", on_click=on_field_selected),
    ),
    Cancel(Const("⬅️ Назад")),
    state=campaign_states.EditCampaignInfo.select_field,
    getter=get_campaign_edit_data,
)

edit_title_window = Window(
    Const("Введите новое название группы:"),
    TextInput(id="edit_title_input", on_success=on_title_edited),
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
        on_success=on_description_edited,
    ),
    SwitchTo(
        Const("⬅️ Назад"),
        id="back_from_description",
        state=campaign_states.EditCampaignInfo.select_field,
    ),
    state=campaign_states.EditCampaignInfo.edit_description,
)

edit_icon_window = Window(
    Const(
        "Для изменения иконки группы создайте новую кампанию с нужной иконкой.\n\n"
        "В будущих версиях здесь будет возможность загрузить новое изображение."
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
        "📝 Название: {campaign_title}\n"
        "📄 Описание: {campaign_description}\n"
        "🖼 Иконка: {icon_status}\n\n"
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
