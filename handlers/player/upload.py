import json
import logging

from aiogram import Router
from aiogram.enums import ContentType
from aiogram.types import Message
from aiogram_dialog import DialogManager, Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Cancel
from aiogram_dialog.widgets.text import Const

from db.models import Character
from services.character_data import update_char_data
from states.upload_character import UploadCharacter

logger = logging.getLogger(__name__)
router = Router()


async def upload_document(msg: Message, _: MessageInput, manager: DialogManager):
    if not msg.document or not msg.document.file_name.endswith(".json"):
        await msg.answer("Отправь .json!")
        logger.warning("User %d didn't send us a valid json", msg.from_user.id)
        return

    f = await msg.bot.download(msg.document.file_id)
    content = f.read()

    source = manager.start_data.get("source")
    user = manager.middleware_data["user"]
    if source == "user":
        source = user
    else:
        source = await Character.get_or_none(id=source)
    if not source:
        logger.error(f"Failed to find source for user %d", user)
        return
    try:
        await update_char_data(source, json.loads(content.decode("utf-8")))
    except json.JSONDecodeError or UnicodeDecodeError:
        logger.warning("User %d sent incorrect json", msg.from_user.id)
        await msg.answer("Это не json, проверь еще раз")
        return

    await msg.answer("Успешно загружено")
    await manager.done()


"""
Этот диалог обязательно должен включать в start_data параметр source,
который должен содержать либо "user", что означает, что нам надо сохранять в юзере, либо же UUID персонажа
"""
router.include_router(
    Dialog(
        Window(
            Const("Отправь нам .json из LSH"),
            Cancel(Const("Отмена")),
            MessageInput(content_types=ContentType.DOCUMENT, func=upload_document),
            state=UploadCharacter.upload,
        ),
    )
)
