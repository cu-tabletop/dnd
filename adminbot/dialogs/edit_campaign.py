import base64
import json
import logging
from aiogram import Router
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram.enums import ContentType
from aiogram_dialog.widgets.kbd import Button, Cancel, SwitchTo, Column
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram.types import CallbackQuery, Message

from services.models import CampaignModelSchema
from services.api_client import api_client
from . import states as campaign_states

logger = logging.getLogger(__name__)


# === Гетеры ===
async def get_campaign_edit_data(dialog_manager: DialogManager, **kwargs):
    campaign_data = dialog_manager.start_data.get("selected_campaign", {})
    dialog_manager.dialog_data["selected_campaign"] = campaign_data

    campaign_data.update(
        dialog_manager.dialog_data.get("new_selected_campaign", {})
    )
    dialog_manager.dialog_data["new_selected_campaign"] = campaign_data
    campaign = CampaignModelSchema(**campaign_data)

    icon = None
    if file_id := campaign.icon:
        icon = MediaAttachment(
            type=ContentType.PHOTO, file_id=MediaId(file_id)
        )

    return {
        "campaign_title": campaign.title,
        "campaign_description": campaign.description or "Описание отсутствует",
        "icon": icon,
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

    dialog_manager.dialog_data["new_selected_campaign"]["title"] = text

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

    dialog_manager.dialog_data["new_selected_campaign"]["description"] = text

    await dialog_manager.switch_to(campaign_states.EditCampaignInfo.confirm)


async def on_icon_entered(
    message: Message, widget: MessageInput, dialog_manager: DialogManager
):
    if message.photo:
        try:
            # Берем фото максимального качества
            photo = message.photo[-1]

            logger.debug(f"Получено фото: {photo.file_id}")
            logger.debug(
                f"Текущее состояние dialog_data: {dialog_manager.dialog_data['new_selected_campaign']}"
            )

            dialog_manager.dialog_data["new_selected_campaign"]["icon"] = (
                photo.file_id
            )

            # dialog_manager.dialog_data["new_selected_campaign"].update(
            #     new_selected_campaign
            # )

            await dialog_manager.switch_to(
                campaign_states.EditCampaignInfo.confirm
            )
        except Exception as e:
            logger.error(f"Error processing photo: {e}")
            await message.answer("❌ Ошибка при обработке изображения")
    else:
        await message.answer("❌ Пожалуйста, отправьте изображение")


async def on_edit_confirm(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    campaign_data_old = dialog_manager.start_data.get("selected_campaign", {})
    campaign_data = dialog_manager.dialog_data.get("new_selected_campaign", {})
    campaign = CampaignModelSchema(**campaign_data_old)

    try:
        result = await api_client.update_campaign(
            telegram_id=callback.from_user.id,
            campaign_id=campaign.id,
            title=campaign_data.get("title"),
            description=campaign_data.get("description"),
            icon=campaign_data.get("icon"),
        )

        if hasattr(result, "error"):
            await callback.answer(
                f"❌ Ошибка: {result.error}", show_alert=True
            )
        else:
            await callback.answer(f"✅ {result.message}", show_alert=True)
            campaign_data_old.update(campaign_data)
            await dialog_manager.done(
                result={"update_data": campaign_data_old.copy()}
            )

    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        await callback.answer(
            "❌ Ошибка при создании кампании", show_alert=True
        )


# === Окна ===
select_field_window = Window(
    DynamicMedia("icon"),
    Multi(
        Format("✏️ Редактирование группы: {campaign_title}"),
        Format("{campaign_description}\n"),
        Const("Выберите что хотите изменить:"),
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
        "🎨 Загрузите иконку для вашей группы:\nОтправьте изображение как фото (не файлом)"
    ),
    MessageInput(func=on_icon_entered, content_types=ContentType.PHOTO),
    SwitchTo(
        Const("⬅️ Назад"),
        id="back_from_icon",
        state=campaign_states.EditCampaignInfo.select_field,
    ),
    state=campaign_states.EditCampaignInfo.edit_icon,
)

confirm_edit_window = Window(
    DynamicMedia("icon"),
    Format(
        "✅ Проверьте изменения:\n\n"
        "📝 Название: {campaign_title}\n"
        "📄 Описание: {campaign_description}\n"
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
