import json

from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Cancel
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from db.models import Campaign, Character, Participation, User
from services.character_data import character_preview_getter
from states.other_games_campaign import OtherGamesCampaign
from states.other_games_character import OtherGamesCharacter

router = Router()


async def character_data_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    character = await Character.get(id=dialog_manager.start_data["character_id"])
    data = json.loads(character.data["data"])

    return character_preview_getter(character, data)


async def on_campaign_info(c: CallbackQuery, b: Button, m: DialogManager):
    user: User = m.middleware_data["user"]
    character = await Character.get(id=m.start_data["character_id"]).prefetch_related("campaign")
    campaign: Campaign = character.campaign
    participation = await Participation.get(user=user, campaign=campaign)
    await m.start(
        OtherGamesCampaign.preview,
        data={
            **m.start_data,
            "campaign_id": campaign.id,
            "participation_id": participation.id,
        },
    )


router.include_router(
    Dialog(
        Window(
            DynamicMedia("avatar", when="avatar"),
            Format("{character_data_preview}", when="character_data_preview"),
            Button(Const("Информация о кампании"), id="campaign_info", on_click=on_campaign_info),
            Cancel(Const("Назад")),
            getter=character_data_getter,
            state=OtherGamesCharacter.preview,
        )
    )
)
