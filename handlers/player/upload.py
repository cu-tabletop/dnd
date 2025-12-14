import json
import logging
from typing import TYPE_CHECKING
from uuid import UUID

from aiogram import Router
from aiogram.enums import ContentType
from aiogram.types import Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Cancel
from aiogram_dialog.widgets.text import Const
from pydantic import BaseModel, field_validator

from db.models import Character
from services.character_data import update_char_data
from states.inventory_view import TargetType
from states.upload_character import UploadCharacter

if TYPE_CHECKING:
    from db.models.base import CharacterData

logger = logging.getLogger(__name__)
router = Router()


class UploadCharacterRequest(BaseModel):
    target_type: TargetType
    target_id: int | UUID | None
    campaign_id: UUID | None = None

    @classmethod
    @field_validator("target_type", mode="before")
    def validate_target_type(cls, v: TargetType | int | str) -> TargetType | None:
        if isinstance(v, TargetType):
            return v
        try:
            if isinstance(v, int):
                return TargetType(v)
            if isinstance(v, str):
                try:
                    return TargetType(int(v))
                except ValueError:
                    return TargetType[v.upper()]
        except (ValueError, KeyError) as e:
            msg = f"Invalid target_type: {v}"
            raise ValueError(msg) from e

    @classmethod
    @field_validator("target_id", mode="wrap")
    def validate_target_id(cls, v: int | UUID | None, values: dict) -> UUID | None | int:
        if "target_type" not in values:
            msg = "target_type is required to be passed"
            raise ValueError(msg)
        target_type: TargetType = values["target_type"]
        if target_type == TargetType.CHARACTER:
            if isinstance(v, UUID) or v is None:
                return v
            msg = "you should provide UUID or None as target_id for CHARACTER target"
            raise ValueError(msg)
        if target_type == TargetType.USER:
            if isinstance(v, int):
                return v
            msg = "you should provide int as target_id for USER target"
            raise ValueError(msg)
        msg = "you provided unrecognized target_type"
        raise ValueError(msg)

    @classmethod
    @field_validator("campaign_id", mode="wrap")
    def validate_campaign_id(cls, v: int | None, values: dict) -> int:
        if "target_type" in values and values["target_type"] == TargetType.CHARACTER and v is None:
            msg = "campaign_id is required for CHARACTER target type"
            raise ValueError(msg)
        return v


async def upload_document(msg: Message, _: MessageInput, manager: DialogManager):
    if not msg.document or not msg.document.file_name.endswith(".json"):
        await msg.answer("Отправь .json!")
        logger.warning("User %d didn't send us a valid json", msg.from_user.id)
        return

    f = await msg.bot.download(msg.document.file_id)
    content = f.read()

    user = manager.middleware_data["user"]
    request = UploadCharacterRequest(**manager.start_data)

    source: CharacterData
    if request.target_type == TargetType.USER:
        source = user
    elif request.target_type == TargetType.CHARACTER:
        if request.target_id is None:
            source = await Character.create(user=user, campaign_id=request.campaign_id)
        else:
            source = await Character.get(id=request.target_id)
    else:
        logger.error("Failed to find source for user %d", user)
        return

    if not source:
        logger.error("Failed to find source for user %d", user)
        return

    try:
        await update_char_data(source, json.loads(content.decode("utf-8")))
    except UnicodeDecodeError:
        logger.warning("Failed to unicode decode payload from user %d", msg.from_user.id)
        await msg.answer("Это не json, проверь еще раз")
        return
    except json.JSONDecodeError:
        logger.warning("User %d sent incorrect json", msg.from_user.id)
        await msg.answer("Это не json, проверь еще раз")
        return

    await msg.answer("Успешно загружено")
    await manager.done()


"""
Этот диалог обязательно должен включать в start_data параметр request: UploadCharacterRequest
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
