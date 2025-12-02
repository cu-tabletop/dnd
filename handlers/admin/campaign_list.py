import logging
from aiogram import Router
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Select, ScrollingGroup, Start
from aiogram_dialog.widgets.text import Const, Format
from aiogram.types import CallbackQuery

from db.models.participation import Participation
from db.models.user import User

from . import states

logger = logging.getLogger(__name__)


# === Гетеры ===
async def get_campaigns_data(dialog_manager: DialogManager, **kwargs):
    user: User = dialog_manager.middleware_data["user"]
    return {
        "campaigns": await Participation.filter(user=user)
        .prefetch_related("campaign")
        .all(),
        "is_admin": user.admin,
    }


# === Кнопки ===
async def on_campaign_selected(
    mes: CallbackQuery,
    wid: Select,
    dialog_manager: DialogManager,
    participation_id,
):
    participation: Participation = await Participation.get(
        id=participation_id
    ).prefetch_related("campaign")
    await dialog_manager.start(
        states.CampaignManage.main,
        data={
            "campaign_id": participation.campaign.id,
            "participation_id": participation.id,
        },
    )


# === Окна ===
campaign_list_window = Window(
    Const("🏰 Магическая Академия - Ваши кампейнами\n\n"),
    ScrollingGroup(
        Select(
            Format("{item.campaign.title}"),
            id="campaign",
            items="campaigns",
            item_id_getter=lambda x: x.id,
            on_click=on_campaign_selected,
        ),
        hide_on_single_page=True,
        height=5,
        id="campaigns",
    ),
    # Const(
    #     "У вас пока нет доступных партий",
    #     when=lambda data, widget, dialog_manager: not data.get("has_campaigns", False),
    # ),
    Start(
        Const("➕ Создать новую"),
        id="create_campaign",
        state=states.CreateCampaign.select_title,
    ),
    Button(
        Const("➕ Создать новую (Для академии)"),
        id="create_verified_campaign",
        on_click=lambda c, b, d: d.start(
            states.CreateCampaign.select_title, data={"verified": True}
        ),
    ),
    state=states.CampaignList.main,
    getter=get_campaigns_data,
)

# === Создание диалога и роутера ===
dialog = Dialog(campaign_list_window)
router = Router()
router.include_router(dialog)
