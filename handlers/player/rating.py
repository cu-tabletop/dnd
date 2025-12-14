import logging

from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format

from db.models import User
from states.player_preview import PlayerPreview
from states.rating import AcademyRating

logger = logging.getLogger(__name__)
router = Router()


async def rating_getter(dialog_manager: DialogManager, **kwargs):
    return {"top": await User.all().order_by("-rating")}


async def on_preview(c: CallbackQuery, b: Button, m: DialogManager, user_id: int):
    await m.start(PlayerPreview.preview, data={"user_id": user_id})


router.include_router(
    Dialog(
        Window(
            Const("Вот топ по рейтингу"),
            ScrollingGroup(
                Select(
                    Format("@{item.username} - {item.rating}"),
                    id="preview",
                    items="top",
                    item_id_getter=lambda x: x.id,
                    on_click=on_preview,
                ),
                hide_on_single_page=True,
                width=1,
                height=5,
                id="top",
            ),
            Cancel(Const("Назад")),
            getter=rating_getter,
            state=AcademyRating.rating,
        ),
    )
)
