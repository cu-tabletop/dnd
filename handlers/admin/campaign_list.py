import logging
from typing import TYPE_CHECKING
from uuid import UUID

from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format

from db.models.participation import Participation
from utils.enums import Mode
from utils.redirect import redirect

from . import states

if TYPE_CHECKING:
    from db.models.user import User

logger = logging.getLogger(__name__)


# === Гетеры ===
async def get_campaigns_data(dialog_manager: DialogManager, **kwargs):
    user: User = dialog_manager.middleware_data["user"]
    if "current_mode" not in dialog_manager.dialog_data:
        value = Mode.Base
        if user.admin:
            value = Mode.Academy
        dialog_manager.dialog_data["current_mode"] = value

    campaigns = (
        await Participation.filter(user=user)
        .prefetch_related("campaign")
        .filter(campaign__verified=dialog_manager.dialog_data["current_mode"] == Mode.Academy)
        .all()
    )
    return {
        "campaigns": campaigns,
        "is_admin": user.admin,
        "has_campaigns": len(campaigns) > 0,
        "view_mode": f"(режим {dialog_manager.dialog_data['current_mode']})" if user.admin else "",
    }


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


async def on_crete_campaign(msg: CallbackQuery, wdg: Button, mng: DialogManager):
    await mng.start(
        state=states.CreateCampaign.select_title, data={"verified": mng.dialog_data.get("mode") == Mode.Academy}
    )


async def on_change_mode(msg: CallbackQuery, wdg: Button, mng: DialogManager):
    mng.dialog_data["current_mode"] = Mode.Academy if mng.dialog_data.get("current_mode") == Mode.Base else Mode.Base
    await mng.show()


# === Окна ===
campaign_list_window = Window(
    Format("🏰 Ваши кампании {view_mode}\n\n"),
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
    Row(
        Button(
            Const("➕ Создать новую"),
            id="create_verified_campaign",
            on_click=on_crete_campaign,
        ),
        Button(
            Const("🔀 Сменить режим"),
            id="change_mode",
            on_click=on_change_mode,
            when="is_admin",
        ),
    ),
    state=states.CampaignList.main,
    getter=get_campaigns_data,
)


# === Создание диалога и роутера ===
dialog = Dialog(campaign_list_window, on_start=redirect)
router = Router()
router.include_router(dialog)
