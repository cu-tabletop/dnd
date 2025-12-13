import logging
from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput, TextInput
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Next, Row
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, Multi
from tortoise.exceptions import IncompleteInstanceError, IntegrityError, OperationalError

from db.models.campaign import Campaign
from db.models.participation import Participation
from services.settings import settings
from utils.role import Role

from . import states

if TYPE_CHECKING:
    from db.models.user import User

logger = logging.getLogger(__name__)


# === Гетеры ===
async def get_confirm_data(dialog_manager: DialogManager, **kwargs):
    icon = None
    if file_id := dialog_manager.dialog_data.get("icon"):
        icon = MediaAttachment(type=ContentType.PHOTO, file_id=MediaId(file_id))

    return {
        "title": dialog_manager.dialog_data.get("title", ""),
        "description": dialog_manager.dialog_data.get("description", "не указано"),
        "icon": icon,
    }


# === Кнопки ===
async def on_title_entered(
    mes: Message,
    wid: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str,
):
    if len(text) > settings.MAX_TITLE_LEN:
        await mes.answer("Максимум 255 символов")
        return
    dialog_manager.dialog_data["title"] = text
    await dialog_manager.next()


async def on_description_entered(
    mes: Message,
    wid: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str,
):
    if len(text) > settings.MAX_DESCRIPTION_LEN:
        mes.answer("Максимум 1023 символа, можно пропустить")
        return
    dialog_manager.dialog_data["description"] = text
    await dialog_manager.next()


async def on_icon_entered(mes: Message, wid: MessageInput, dialog_manager: DialogManager):
    if mes.photo:
        photo = mes.photo[-1]
        file = await mes.bot.get_file(photo.file_id)
        await mes.bot.download_file(file.file_path)
        settings.minio.append_object()
        dialog_manager.dialog_data["icon"] = photo.file_id

        await dialog_manager.next()
    else:
        await mes.answer("❌ Пожалуйста, отправьте изображение")


async def on_confirm(mes: CallbackQuery, button: Button, dialog_manager: DialogManager):
    campaign_data = dialog_manager.dialog_data
    user: User = dialog_manager.middleware_data["user"]

    try:
        verified = False
        if isinstance(dialog_manager.start_data, dict):
            verified = dialog_manager.start_data.get("verified", False)

        new_campaign: Campaign = await Campaign.create(
            title=campaign_data.get("title", ""),
            description=campaign_data.get("description", ""),
            icon=campaign_data.get("icon", ""),
            verified=verified,
        )

        await Participation.create(user=user, campaign=new_campaign, role=Role.OWNER)

        await mes.answer(
            f"✅ {new_campaign.title} успешно создан",
            show_alert=True,
        )
        await dialog_manager.done()

    except (OperationalError, IntegrityError, IncompleteInstanceError) as e:
        logger.exception("Error creating campaign", exc_info=e)
        await mes.answer("❌ Ошибка при создании кампании", show_alert=True)


async def on_cancel(mes: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await mes.answer("Создание кампании отменено")
    await dialog_manager.done()


# === Окна ===
title_window = Window(
    Const("🏰 Создание новой кампании\n\nВведите название кампании:\n(максимум 255 символов)"),
    TextInput(
        id="title_input",
        on_success=on_title_entered,
    ),
    Cancel(Const("❌ Отмена"), on_click=on_cancel),
    state=states.CreateCampaign.select_title,
)

description_window = Window(
    Multi(
        Const("📝 Теперь введите описание кампании:\n"),
        Format("Название: {title}\n"),
        Const("(максимум 1023 символа, можно пропустить)"),
    ),
    TextInput(
        id="description_input",
        on_success=on_description_entered,
    ),
    Row(
        Back(Const("⬅️ Назад")),
        Next(Const("Пропустить ⏩")),
    ),
    Cancel(Const("❌ Отмена"), on_click=on_cancel),
    state=states.CreateCampaign.select_description,
    getter=get_confirm_data,
)

icon_window = Window(
    Multi(
        Const("🎨 Загрузите иконку для вашей кампании:\n"),
        Format("Название: {title}\n"),
        Format("Описание: {description}\n\n"),
        Const("Отправьте изображение как фото (не файлом)"),
    ),
    MessageInput(func=on_icon_entered, content_types=ContentType.PHOTO),
    Row(
        Back(Const("⬅️ Назад")),
        Next(Const("Пропустить ⏩")),
    ),
    Cancel(Const("❌ Отмена"), on_click=on_cancel),
    state=states.CreateCampaign.select_icon,
    getter=get_confirm_data,
)

confirm_window = Window(
    DynamicMedia("icon"),
    Multi(
        Const("✅ Проверьте данные нового кампании:\n\n"),
        Format("📝 Название: {title}"),
        Format("📄 Описание: {description}"),
        Const("Всё верно?"),
        sep="\n",
    ),
    Button(
        Const("✅ Создать кампанию"),
        id="confirm_create",
        on_click=on_confirm,
    ),
    Back(Const("⬅️ Назад")),
    Cancel(Const("❌ Отмена"), on_click=on_cancel),
    state=states.CreateCampaign.confirm,
    getter=get_confirm_data,
)

# === Создание диалога и роутера ===
dialog = Dialog(title_window, description_window, icon_window, confirm_window)
router = Router()
router.include_router(dialog)
