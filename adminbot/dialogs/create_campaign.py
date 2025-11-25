import json
import logging
import base64
import tempfile
import os

from aiogram import Router
from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.kbd import Button, Back, Cancel, Row
from aiogram_dialog.widgets.text import Const, Format, Multi

from services.api_client import api_client
from . import states as campaign_states

router = Router()
logger = logging.getLogger(__name__)


# === Гетеры ===
async def get_confirm_data(dialog_manager: DialogManager, **kwargs):
    logger.debug(dialog_manager.dialog_data)

    # Готовим текст статуса иконки заранее
    icon_status = (
        "загружена"
        if dialog_manager.dialog_data.get("icon")
        else "не установлена"
    )

    return {
        "title": dialog_manager.dialog_data.get("title", ""),
        "description": dialog_manager.dialog_data.get(
            "description", "не указано"
        ),
        "icon_status": icon_status,
    }


# === Кнопки ===
async def on_title_entered(
    message: Message,
    widget: TextInput,
    dialog_manager: DialogManager,
    text: str,
):
    dialog_manager.dialog_data["title"] = text
    await dialog_manager.next()


async def on_description_entered(
    message: Message,
    widget: TextInput,
    dialog_manager: DialogManager,
    text: str,
):
    dialog_manager.dialog_data["description"] = text
    await dialog_manager.next()


async def on_icon_entered(
    message: Message, widget: MessageInput, dialog_manager: DialogManager
):
    if message.photo:
        try:
            # Берем фото максимального качества
            photo = message.photo[-1]

            # Скачиваем фото
            file = await message.bot.get_file(photo.file_id)
            photo_bytes = await message.bot.download_file(file.file_path)

            # Конвертируем в base64
            icon_base64 = base64.b64encode(photo_bytes.read()).decode("utf-8")
            dialog_manager.dialog_data["icon"] = icon_base64

            await dialog_manager.next()
        except Exception as e:
            logger.error(f"Error processing photo: {e}")
            await message.answer("❌ Ошибка при обработке изображения")
    else:
        await message.answer("❌ Пожалуйста, отправьте изображение")


async def on_skip_description(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    dialog_manager.dialog_data["description"] = ""
    await dialog_manager.next()


async def on_skip_icon(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    dialog_manager.dialog_data["icon"] = None
    await dialog_manager.next()


async def on_confirm(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    campaign_data = dialog_manager.dialog_data

    try:
        result = await api_client.create_campaign(
            telegram_id=callback.from_user.id,
            title=campaign_data.get("title", ""),
            description=campaign_data.get("description"),
            icon=campaign_data.get("icon"),
        )

        if hasattr(result, "error"):
            await callback.answer(
                f"❌ Ошибка: {result.error}", show_alert=True
            )
        else:
            await callback.answer(f"✅ {result.message}", show_alert=True)
            await dialog_manager.done()

    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        await callback.answer(
            "❌ Ошибка при создании кампании", show_alert=True
        )


async def on_cancel(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    await callback.message.answer("Создание кампании отменено")
    await dialog_manager.done()


# === Окна ===
title_window = Window(
    Const(
        "🏰 Создание новой учебной группы\n\n"
        "Введите название для вашей учебной группы:\n"
        "(максимум 255 символов)"
    ),
    TextInput(
        id="title_input",
        on_success=on_title_entered,
    ),
    Cancel(Const("Отмена")),
    state=campaign_states.CreateCampaign.select_title,
)

description_window = Window(
    Multi(
        Const("📝 Теперь введите описание для вашей группы:\n"),
        Format("Название: {title}\n"),
        Const("(максимум 1023 символа, можно пропустить)"),
    ),
    TextInput(
        id="description_input",
        on_success=on_description_entered,
    ),
    Row(
        Button(
            Const("Пропустить"),
            id="skip_desc",
            on_click=on_skip_description,
        ),
        Back(Const("Назад")),
    ),
    Cancel(Const("Отмена")),
    state=campaign_states.CreateCampaign.select_description,
    getter=get_confirm_data,
)

icon_window = Window(
    Multi(
        Const("🎨 Загрузите иконку для вашей группы:\n"),
        Format("Название: {title}\n"),
        Format("Описание: {description}\n\n"),
        Const("Отправьте изображение как фото (не файлом)"),
    ),
    MessageInput(func=on_icon_entered, content_types=ContentType.PHOTO),
    Row(
        Button(Const("Пропустить"), id="skip_icon", on_click=on_skip_icon),
        Back(Const("Назад")),
    ),
    Cancel(Const("Отмена")),
    state=campaign_states.CreateCampaign.select_icon,
    getter=get_confirm_data,
)

confirm_window = Window(
    Multi(
        Const("✅ Проверьте данные новой учебной группы:\n\n"),
        Format("📝 Название: {title}"),
        Format("📄 Описание: {description}"),
        Format("🖼 Иконка: {icon_status}"),
        Const(""),
        Const("Всё верно?"),
        sep="\n",
    ),
    Button(
        Const("✅ Создать группу"),
        id="confirm_create",
        on_click=on_confirm,
    ),
    Back(Const("⬅️ Назад")),
    Cancel(Const("❌ Отмена")),
    state=campaign_states.CreateCampaign.confirm,
    getter=get_confirm_data,
)

# === Создание диалога и роутера ===
dialog = Dialog(title_window, description_window, icon_window, confirm_window)
router = Router()
router.include_router(dialog)
