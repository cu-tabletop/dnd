import logging
from uuid import UUID

from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format

from db.models import Campaign, Participation
from states.academy_campaigns import AcademyCampaignPreview, AcademyCampaigns
from utils.redirect import redirect

logger = logging.getLogger(__name__)
router = Router()


async def campaigns_getter(dialog_manager: DialogManager, **kwargs):
    user = dialog_manager.middleware_data["user"]
    return {
        "campaigns": await Participation.filter(user=user, campaign__verified=True).prefetch_related("campaign").all()
    }


async def on_campaign(c: CallbackQuery, b: Button, m: DialogManager, participation_id: UUID):
    participation = await Participation.get(id=participation_id).prefetch_related("campaign")
    await m.start(
        AcademyCampaignPreview.preview,
        data={"campaign_id": participation.campaign.id, "participation_id": participation.id},
    )


async def campaign_getter(dialog_manager: DialogManager, **kwargs):
    campaign = await Campaign.get(id=dialog_manager.start_data["campaign_id"])
    return {
        "title": campaign.title,
        "description": campaign.description,
    }


router.include_router(
    Dialog(
        Window(
            Const("Кампании внутри академии, в которых вы участвуете"),
            ScrollingGroup(
                Select(
                    Format("{item.campaign.title}"),
                    id="campaign",
                    items="campaigns",
                    item_id_getter=lambda x: x.id,
                    on_click=on_campaign,
                ),
                hide_on_single_page=True,
                height=5,
                id="campaigns",
            ),
            Cancel(Const("Назад")),
            getter=campaigns_getter,
            state=AcademyCampaigns.campaigns,
        ),
        on_start=redirect,
    )
)


router.include_router(
    Dialog(
        Window(
            Const("Инфа о кампании"),
            Format("{title}\n{description}"),
            Cancel(Const("Назад")),
            getter=campaign_getter,
            state=AcademyCampaignPreview.preview,
        ),
        on_start=redirect,
    )
)
