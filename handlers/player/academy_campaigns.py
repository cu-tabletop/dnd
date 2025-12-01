import json
import logging

import tortoise.exceptions
from aiogram import Router
from aiogram.enums import ContentType
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, Dialog, Window
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import Column, Button, Cancel, ScrollingGroup, Select, Url, Back
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

router.include_router(Dialog(Window(
    Const("Кампании внутри академии"),
    Cancel(Const("Назад")),
    state=AcademyCampaigns.campaigns
)))
