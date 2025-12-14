import logging
from typing import TYPE_CHECKING
from uuid import UUID

from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select, Start
from aiogram_dialog.widgets.text import Const, Format

from db.models.participation import Participation
from utils.redirect import redirect

from . import states

if TYPE_CHECKING:
    from db.models.user import User

logger = logging.getLogger(__name__)


# === Гетеры ===
async def get_campaigns_data(dialog_manager: DialogManager, **kwargs):
    user: User = dialog_manager.middleware_data["user"]
    campaigns = await Participation.filter(user=user).prefetch_related("campaign").all()
    return {"campaigns": campaigns, "is_admin": user.admin, "has_campaigns": len(campaigns) > 0}


# === Кнопки ===
async def on_campaign_selected(
    mes: CallbackQuery,
    wid: Select,
    dialog_manager: DialogManager,
    participation_id: UUID,
):
    participation: Participation = await Participation.get(id=participation_id).prefetch_related("campaign")
    await dialog_manager.start(
        states.CampaignManage.main,
        data={
            "campaign_id": participation.campaign.id,
            "participation_id": participation.id,
        },
    )


# === Окна ===
campaign_list_window = Window(
    Const("🏰 Ваши кампании\n\n"),
    Const(
        "У вас пока нет доступных кампаний",
        when=lambda data, widget, dialog_manager: not data.get("has_campaigns", False),
    ),
    ScrollingGroup(
        Select(
            Format("{item.campaign.title}"),
            id="campaign",
            items="campaigns",
            item_id_getter=lambda x: x.id,
            on_click=on_campaign_selected,
            type_factory=UUID,
        ),
        hide_on_single_page=True,
        width=1,
        height=5,
        id="campaigns",
    ),
    Start(
        Const("➕ Создать новую"),
        id="create_campaign",
        state=states.CreateCampaign.select_title,
    ),
    Button(
        Const("➕ Создать новую (Для академии)"),
        id="create_verified_campaign",
        on_click=lambda c, b, d: d.start(states.CreateCampaign.select_title, data={"verified": True}),
        when="is_admin",
    ),
    state=states.CampaignList.main,
    getter=get_campaigns_data,
)


# === Создание диалога и роутера ===
dialog = Dialog(campaign_list_window, on_start=redirect)
router = Router()
router.include_router(dialog)
