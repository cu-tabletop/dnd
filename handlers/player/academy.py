import json
import logging

from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, Column
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from services.character_data import character_preview_getter
from states.academy import Academy
from states.academy_campaigns import AcademyCampaigns
from states.inventory_view import InventoryView, TargetType
from states.rating import AcademyRating
from states.upload_character import UploadCharacter
from utils.redirect import redirect

logger = logging.getLogger(__name__)
router = Router()


async def on_inventory(c: CallbackQuery, b: Button, m: DialogManager):
    await m.start(InventoryView.view, data={"target_type": TargetType.USER, "target_id": m.middleware_data["user"].id})


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
        ),
        on_start=redirect,
    )
)
