import json
import logging

import tortoise.exceptions
from aiogram import Router
from aiogram.enums import ContentType
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, Dialog, Window
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import Column, Button, Cancel
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from db.models import Invite, User
from services.character import CharacterData, parse_character_data
from services.character_data import character_preview_getter
from states.academy import Academy
from states.academy_campaigns import AcademyCampaigns
from states.rating import AcademyRating
from states.start_simple import StartSimple
from states.upload_character import UploadCharacter

logger = logging.getLogger(__name__)
router = Router()


async def on_inventory(c: CallbackQuery, b: Button, m: DialogManager): ...


async def on_update(c: CallbackQuery, b: Button, m: DialogManager):
    await m.start(UploadCharacter.upload, data={"source": "user"})


async def on_rating(c: CallbackQuery, b: Button, m: DialogManager):
    await m.start(AcademyRating.rating)


async def on_campaigns(c: CallbackQuery, b: Button, m: DialogManager):
    await m.start(AcademyCampaigns.campaigns)


async def character_data_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    user = dialog_manager.middleware_data["user"]
    data = json.loads(user.data["data"])

    return character_preview_getter(user, data)


router.include_router(
    Dialog(
        Window(
            DynamicMedia("avatar", when="avatar"),
            Format("{character_data_preview}", when="character_data_preview"),
            Column(
                Button(Const("Посмотреть инвентарь"), id="inventory", on_click=on_inventory),
                Button(Const("Загрузить обновленный .json"), id="update_json", on_click=on_update),
                Button(Const("Рейтинг"), id="rating", on_click=on_rating),
                Button(Const("Кампании внутри академии"), id="campaigns", on_click=on_campaigns),
                Cancel(Const("Назад")),
            ),
            getter=character_data_getter,
            state=Academy.main,
        )
    )
)
