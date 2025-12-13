import logging

from aiogram import Router
from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput, TextInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Column, SwitchTo
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, Multi
from tortoise.exceptions import ConfigurationError, OperationalError

from db.models.campaign import Campaign
from db.models.participation import Participation
from services.settings import settings
from utils.role import Role

from . import states

logger = logging.getLogger(__name__)


# === Гетеры ===
async def get_campaign_edit_data(dialog_manager: DialogManager, **kwargs):
    logger.debug("Переданные данные в edit_campaign: %s", dialog_manager.start_data)

    if "campaign_id" not in dialog_manager.dialog_data and isinstance(dialog_manager.start_data, dict):
        dialog_manager.dialog_data["campaign_id"] = dialog_manager.start_data["campaign_id"]
        dialog_manager.dialog_data["participation_id"] = dialog_manager.start_data["participation_id"]

    campaign = await Campaign.get(id=dialog_manager.dialog_data["campaign_id"])
    participation = await Participation.get(id=dialog_manager.dialog_data["participation_id"])

    if "new_data" not in dialog_manager.dialog_data:
        dialog_manager.dialog_data["new_data"] = {}

    icon = None
    if file_id := dialog_manager.dialog_data["new_data"].get("icon", campaign.icon):
        icon = MediaAttachment(type=ContentType.PHOTO, file_id=MediaId(file_id))

    return {
        "campaign_title": dialog_manager.dialog_data["new_data"].get("title", campaign.title),
        "campaign_description": dialog_manager.dialog_data["new_data"].get("description", campaign.description),
        "icon": icon,
        "is_owner": participation.role == Role.OWNER,
    }


# === Кнопки ===
async def on_field_selected(mes: CallbackQuery, wid: Button, dialog_manager: DialogManager):
    field_map = {
        "title": states.EditCampaignInfo.edit_title,
        "description": states.EditCampaignInfo.edit_description,
        "icon": states.EditCampaignInfo.edit_icon,
        "delete": states.EditCampaignInfo.confirm_delete,
    }
    if wid.widget_id in field_map:
        await dialog_manager.switch_to(field_map[wid.widget_id])


async def on_title_edited(
    mes: Message,
    wid: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str,
):
    if len(text) > settings.MAX_TITLE_LEN:
        await mes.answer("Название слишком длинное (максимум 255 символов)")
        return

    dialog_manager.dialog_data["new_data"]["title"] = text

    await dialog_manager.switch_to(states.EditCampaignInfo.confirm)


async def on_description_edited(
    mes: Message,
    wid: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str,
):
    if len(text) > settings.MAX_DESCRIPTION_LEN:
        await mes.answer("Описание слишком длинное (максимум 1023 символа)")
        return

    dialog_manager.dialog_data["new_data"]["description"] = text

    await dialog_manager.switch_to(states.EditCampaignInfo.confirm)


async def on_icon_entered(mes: Message, wid: MessageInput, dialog_manager: DialogManager):
    if mes.photo:
        photo = mes.photo[-1]

        dialog_manager.dialog_data["new_data"]["icon"] = photo.file_unique_id

        await dialog_manager.switch_to(states.EditCampaignInfo.confirm)
    else:
        await mes.answer("❌ Пожалуйста, отправьте изображение")


async def on_edit_confirm(mes: CallbackQuery, wid: Button, dialog_manager: DialogManager):
    try:
        campaign = await Campaign.get(id=dialog_manager.dialog_data.get("campaign_id", 0))
        new_data = dialog_manager.dialog_data.get("new_data", {})

        campaign = await Campaign.update_from_dict(campaign, new_data)

        await campaign.save()

        await mes.answer(f"✅ {campaign.title} успешно обновлён", show_alert=True)
        await dialog_manager.done()

    except (ValueError, ConfigurationError) as e:
        logger.exception("Error creating campaign", exc_info=e)
        await mes.answer("❌ Ошибка при обновлении", show_alert=True)


async def on_remove_campaign(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    campaign: Campaign = await Campaign.get(id=dialog_manager.dialog_data["campaign_id"])

    try:
        title = campaign.title
        await campaign.delete()
        await callback.answer(
            f"✅ Кампания {title} удалена",
            show_alert=True,
        )
        await dialog_manager.done({"deleted": True})
    except OperationalError as e:
        logger.exception("Error processing delete campaign", exc_info=e)
        await callback.answer("❌ Ошибка при удалении", show_alert=True)


# === Окна ===
select_field_window = Window(
    DynamicMedia("icon"),
    Multi(
        Format("⚙️ Настройки кампании: {campaign_title}"),
        Format("📄 Описание: {campaign_description}"),
        Const("\nВыберите что хотите изменить:"),
    ),
    Column(
        Button(Const("✏️ Изменить название"), id="title", on_click=on_field_selected),
        Button(
            Const("📝 Изменить описание"),
            id="description",
            on_click=on_field_selected,
        ),
        Button(Const("🎨 Изменить иконку"), id="icon", on_click=on_field_selected),
        Button(
            Const("🗑️ Удаление кампании"),
            id="delete",
            on_click=on_field_selected,
            when="is_owner",
        ),
    ),
    Cancel(Const("⬅️ Назад")),
    state=states.EditCampaignInfo.select_field,
    getter=get_campaign_edit_data,
)

edit_title_window = Window(
    Const("Введите новое название:"),
    TextInput(id="edit_title_input", on_success=on_title_edited),
    SwitchTo(
        Const("⬅️ Назад"),
        id="back_from_title",
        state=states.EditCampaignInfo.select_field,
    ),
    state=states.EditCampaignInfo.edit_title,
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
        state=states.EditCampaignInfo.select_field,
    ),
    state=states.EditCampaignInfo.edit_description,
)

edit_icon_window = Window(
    Const("🎨 Загрузите иконку для вашей кампании:\nОтправьте изображение как фото (не файлом)"),
    MessageInput(func=on_icon_entered, content_types=ContentType.PHOTO),
    SwitchTo(
        Const("⬅️ Назад"),
        id="back_from_icon",
        state=states.EditCampaignInfo.select_field,
    ),
    state=states.EditCampaignInfo.edit_icon,
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
        state=states.EditCampaignInfo.select_field,
    ),
    Cancel(Const("❌ Отмена")),
    state=states.EditCampaignInfo.confirm,
    getter=get_campaign_edit_data,
)
confirm_delete_window = Window(
    Format("⚠️ Вы точно хотите удалить кампанию?\n\n<b>{campaign_title}</b>\n\nЭто действие нельзя отменить!"),
    Button(Const("🚫 Удалить кампанию"), id="remove_campaign", on_click=on_remove_campaign),
    SwitchTo(
        Const("⬅️ Отмена"),
        id="back",
        state=states.EditCampaignInfo.select_field,
    ),
    state=states.EditCampaignInfo.confirm_delete,
    getter=get_campaign_edit_data,
)
# === Создание диалога и роутера ===
dialog = Dialog(
    select_field_window,
    edit_title_window,
    edit_description_window,
    edit_icon_window,
    confirm_edit_window,
    confirm_delete_window,
)
router = Router()
router.include_router(dialog)
