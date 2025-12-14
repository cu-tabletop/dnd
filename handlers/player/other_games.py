import json
from uuid import UUID

from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format

from db.models import Campaign, Character, Participation, User
from states.other_games import OtherGames
from states.other_games_campaign import OtherGamesCampaign
from states.other_games_character import OtherGamesCharacter
from utils.character import CharacterData, parse_character_data

router = Router()


async def main_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    user: User = dialog_manager.middleware_data["user"]

    characters: list[Character] = (
        await Character.filter(user=user, campaign__verified=False).prefetch_related("campaign").all()
    )

    characters_data: list[tuple[Character, CharacterData, Campaign]] = [
        (character, parse_character_data(json.loads(character.data["data"])), character.campaign)
        for character in characters
    ]

    return {
        "characters_data": characters_data,
        "has_characters": len(characters_data) > 0,
    }


async def available_campaigns_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    user: User = dialog_manager.middleware_data["user"]

    participations: list[tuple[Campaign, Participation]] = [
        (p.campaign, p)
        for p in (await Participation.filter(user=user, campaign__verified=False).prefetch_related("campaign").all())
    ]

    return {"participations": participations, "participations_exist": len(participations) > 0}


async def on_character_selected(c: CallbackQuery, b: Button, m: DialogManager, character_id: UUID):
    await m.start(
        OtherGamesCharacter.preview,
        data={
            "character_id": character_id,
        },
    )


async def on_available_games(c: CallbackQuery, b: Button, m: DialogManager):
    await m.switch_to(OtherGames.available)


async def on_campaign_selected(c: CallbackQuery, b: Button, m: DialogManager, participation_id: UUID):
    user: User = m.middleware_data["user"]
    participation = await Participation.get(id=participation_id).prefetch_related("campaign")
    campaign: Campaign = participation.campaign
    character = await Character.get_or_none(user=user, campaign=campaign)
    if character is None:
        await m.start(
            OtherGamesCampaign.preview, data={"campaign_id": campaign.id, "participation_id": participation.id}
        )
    else:
        ...


router.include_router(
    Dialog(
        Window(
            Const("Вы находитесь в меню неофициальных игр"),
            ScrollingGroup(
                Select(
                    Format("{item[1].name} - {item[2].title}"),
                    id="character_select",
                    items="characters_data",
                    item_id_getter=lambda c: c[0].id,
                    on_click=on_character_selected,
                    type_factory=UUID,
                ),
                id="characters_scroll",
                width=1,
                height=8,
                hide_on_single_page=True,
                when="has_characters",
            ),
            Button(Const("Посмотреть доступные кампании"), id="available_games", on_click=on_available_games),
            Cancel(Const("Назад")),
            getter=main_getter,
            state=OtherGames.main,
        ),
        Window(
            Const("Вот кампании к которым у вас есть доступ"),
            ScrollingGroup(
                Select(
                    Format("{item[0].title} - {item[1].role.name}"),
                    id="campaign_select",
                    items="participations",
                    item_id_getter=lambda c: c[1].id,
                    on_click=on_campaign_selected,
                    type_factory=UUID,
                ),
                id="participations_scroll",
                width=1,
                height=8,
                hide_on_single_page=True,
                when="participations_exist",
            ),
            Back(Const("Назад")),
            getter=available_campaigns_getter,
            state=OtherGames.available,
        ),
    )
)
