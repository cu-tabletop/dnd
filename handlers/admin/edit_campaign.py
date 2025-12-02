import logging
from aiogram import Router
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram.enums import ContentType, ParseMode
from aiogram_dialog.widgets.kbd import Button, Cancel, SwitchTo, Column
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram_dialog.widgets.input import TextInput, MessageInput, ManagedTextInput
from aiogram.types import CallbackQuery, Message

from db.models.campaign import Campaign

from . import states as campaign_states

logger = logging.getLogger(__name__)


# === Гетеры ===
async def get_campaign_edit_data(dialog_manager: DialogManager, **kwargs):
    logger.debug(f"Переданные данные в edit_campaign: {dialog_manager.start_data}")
    if "campaign_id" not in dialog_manager.dialog_data:
        if isinstance(dialog_manager.start_data, dict):

            dialog_manager.dialog_data["campaign_id"] = dialog_manager.start_data.get(
                "campaign_id", 0
            )
            dialog_manager.dialog_data["participation_id"] = (
                dialog_manager.start_data.get("participation_id", 0)
            )

    campaign = await Campaign.get(id=dialog_manager.dialog_data.get("campaign_id", 0))

    if "new_data" not in dialog_manager.dialog_data:
        dialog_manager.dialog_data["new_data"] = dict()

    icon = None
    if file_id := dialog_manager.dialog_data["new_data"].get("icon", campaign.icon):
        icon = MediaAttachment(type=ContentType.PHOTO, file_id=MediaId(file_id))

    logger.debug(f"Значение icon: {icon}")

    return {
        "campaign_title": dialog_manager.dialog_data["new_data"].get(
            "title", campaign.title
        ),
        "campaign_description": dialog_manager.dialog_data["new_data"].get(
            "description", campaign.description
        ),
        "icon": icon,
    }


# === Кнопки ===
async def on_field_selected(
    mes: CallbackQuery, wid: Button, dialog_manager: DialogManager
):
    field_map = {
        "title": campaign_states.EditCampaignInfo.edit_title,
        "description": campaign_states.EditCampaignInfo.edit_description,
        "icon": campaign_states.EditCampaignInfo.edit_icon,
    }
    if wid.widget_id in field_map:
        await dialog_manager.switch_to(field_map[wid.widget_id])


async def on_title_edited(
    mes: Message,
    wid: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str,
):
    if len(text) > 255:
        await mes.answer("Название слишком длинное (максимум 255 символов)")
        return

    dialog_manager.dialog_data["new_data"]["title"] = text

    await dialog_manager.switch_to(campaign_states.EditCampaignInfo.confirm)


async def on_description_edited(
    mes: Message,
    wid: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str,
):
    if len(text) > 1023:
        await mes.answer("Описание слишком длинное (максимум 1023 символа)")
        return

    dialog_manager.dialog_data["new_data"]["description"] = text

    await dialog_manager.switch_to(campaign_states.EditCampaignInfo.confirm)


async def on_icon_entered(
    mes: Message, wid: MessageInput, dialog_manager: DialogManager
):
    if mes.photo:
        try:
            photo = mes.photo[-1]

            dialog_manager.dialog_data["new_data"]["icon"] = photo.file_id

            await dialog_manager.switch_to(campaign_states.EditCampaignInfo.confirm)
        except Exception as e:
            logger.error(f"Error processing photo: {e}")
            await mes.answer("❌ Ошибка при обработке изображения")
    else:
        await mes.answer("❌ Пожалуйста, отправьте изображение")


async def on_edit_confirm(
    mes: CallbackQuery, wid: Button, dialog_manager: DialogManager
):
    try:
        campaign = await Campaign.get(
            id=dialog_manager.dialog_data.get("campaign_id", 0)
        )
        new_data = dialog_manager.dialog_data.get("new_data", {})

        campaign = await Campaign.update_from_dict(campaign, new_data)

        await campaign.save()

        await mes.answer(f"✅ {campaign.title} успешно обновлён", show_alert=True)
        await dialog_manager.done()

    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        await mes.answer("❌ Ошибка при обновлении", show_alert=True)


# === Окна ===
select_field_window = Window(
    DynamicMedia("icon"),
    Multi(
        Format("✏️ Редактирование: {campaign_title}"),
        Format("📜 Описание: {campaign_description}"),
        Const("Выберите что хотите изменить:"),
    ),
    Column(
        Button(Const("📝 Название"), id="title", on_click=on_field_selected),
        Button(
            Const("📄 Описание"),
            id="description",
            on_click=on_field_selected,
        ),
        Button(Const("🎨 Иконка"), id="icon", on_click=on_field_selected),
    ),
    Cancel(Const("⬅️ Назад")),
    state=campaign_states.EditCampaignInfo.select_field,
    getter=get_campaign_edit_data,
    # parse_mode=ParseMode.MARKDOWN_V2,
)

edit_title_window = Window(
    Const("Введите новое название:"),
    TextInput(id="edit_title_input", on_success=on_title_edited),
    SwitchTo(
        Const("⬅️ Назад"),
        id="back_from_title",
        state=campaign_states.EditCampaignInfo.select_field,
    ),
    state=campaign_states.EditCampaignInfo.edit_title,
)

edit_description_window = Window(
    Const("Введите новое описание:"),
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
    Const("🎨 Загрузите иконку для вашей:\nОтправьте изображение как фото (не файлом)"),
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
    Multi(
        Format(
            "✅ Проверьте изменения:\n\n"
            "📝 Название: {campaign_title}\n"
            "📄 Описание: {campaign_description}\n"
            "Сохранить изменения?"
        )
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
