from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Cancel
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from db.models import Character
from services.campaigns import campaign_getter
from states.inventory_view import TargetType
from states.other_games_campaign import OtherGamesCampaign
from states.upload_character import UploadCharacter

router = Router()


async def campaign_preview_getter(dialog_manager: DialogManager, **kwargs):
    campaign_id = dialog_manager.start_data.get("campaign_id")
    user = dialog_manager.middleware_data["user"]

    character: Character | None = await Character.get_or_none(campaign_id=campaign_id, user=user)
    return {
        **await campaign_getter(dialog_manager, **kwargs),
        "should_join": character is None,
    }


async def on_join_campaign(c: CallbackQuery, b: Button, m: DialogManager):
    await m.start(
        UploadCharacter.upload,
        data={
            "target_type": TargetType.CHARACTER,
            "target_id": None,
            "campaign_id": m.start_data.get("campaign_id"),
        },
    )


router.include_router(
    Dialog(
        Window(
            Format("Информация о кампании: {title}\n\nОписание: {description}\n\nВыберите действие:"),
            DynamicMedia("icon"),
            Button(Const("Присоединиться"), id="join", on_click=on_join_campaign, when="should_join"),
            Cancel(Const("Назад")),
            getter=campaign_preview_getter,
            state=OtherGamesCampaign.preview,
        )
    )
)
