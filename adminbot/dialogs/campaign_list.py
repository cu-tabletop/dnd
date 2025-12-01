import logging
from aiogram import Router
from aiogram_dialog import Dialog, Window, DialogManager, SubManager
from aiogram_dialog.widgets.kbd import Button, Group, Row, ListGroup, Select
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram.types import CallbackQuery

from services.api_client import api_client
from . import states as campaign_states

logger = logging.getLogger(__name__)


# === Гетеры ===
async def get_campaigns_data(dialog_manager: DialogManager, **kwargs):
    user_id = dialog_manager.start_data.get("user_id")
    page = dialog_manager.dialog_data.get("page", 0)
    campaigns_per_page = 5

    campaigns = await api_client.get_campaigns(user_id=user_id)

    logger.debug(f"Полученные компейны: {campaigns}")

    if not campaigns:
        return {
            "campaigns": [],
            "current_page": 1,
            "total_pages": 1,
            "has_prev": False,
            "has_next": False,
            "has_campaigns": False,
        }

    start_idx = page * campaigns_per_page
    end_idx = start_idx + campaigns_per_page
    current_campaigns = campaigns[start_idx:end_idx]

    total_pages = (
        len(campaigns) + campaigns_per_page - 1
    ) // campaigns_per_page

    return {
        "campaigns": current_campaigns,
        "current_page": page + 1,
        "total_pages": total_pages,
        "has_prev": page > 0,
        "has_next": end_idx < len(campaigns),
        "has_campaigns": len(campaigns) > 0,
    }


# === Кнопки ===
async def on_campaign_selected(
    callback: CallbackQuery, button: Button, manager: SubManager
):
    campaign_id = manager.item_id
    logger.info(f"Selected campaign ID: {campaign_id}")

    campaigns_data = await get_campaigns_data(manager)
    selected_campaign = next(
        (
            camp
            for camp in campaigns_data["campaigns"]
            if str(camp.id) == campaign_id
        ),
        None,
    )

    if selected_campaign:
        manager.dialog_data["selected_campaign"] = (
            selected_campaign.model_dump()
        )

    await manager.start(
        campaign_states.CampaignManage.main,
        data={"selected_campaign": selected_campaign.model_dump()},
    )


async def on_page_change(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    direction: int,
):
    current_page = dialog_manager.dialog_data.get("page", 0)
    campaigns_data = await get_campaigns_data(dialog_manager)
    total_pages = campaigns_data["total_pages"]

    new_page = current_page + direction
    if 0 <= new_page < total_pages:
        dialog_manager.dialog_data["page"] = new_page
        await dialog_manager.update({})


# === Окна ===
campaign_list_window = Window(
    Multi(
        Const("🏰 Магическая Академия - Управление кампейнами\n\n"),
        Format("Страница {current_page}/{total_pages}\n"),
    ),
    ListGroup(
        Button(
            Format("{item.title}"),
            id="campaign",
            on_click=on_campaign_selected,
        ),
        item_id_getter=lambda item: str(item.id),
        items="campaigns",
        id="campaigns_group",
        when="has_campaigns",
    ),
    Const(
        "У вас пока нет доступных партий",
        when=lambda data, widget, manager: not data.get(
            "has_campaigns", False
        ),
    ),
    Group(
        Row(
            Button(
                Const("⬅️"),
                id="prev_page",
                on_click=lambda c, b, d: on_page_change(c, b, d, -1),
                when="has_prev",
            ),
            Button(
                Const("➡️"),
                id="next_page",
                on_click=lambda c, b, d: on_page_change(c, b, d, 1),
                when="has_next",
            ),
        ),
        Button(
            Const("➕ Создать новую"),
            id="create_campaign",
            on_click=lambda c, b, d: d.start(
                campaign_states.CreateCampaign.select_title
            ),
        ),
        width=2,
    ),
    state=campaign_states.CampaignManagerMain.main,
    getter=get_campaigns_data,
)

# === Создание диалога и роутера ===
dialog = Dialog(campaign_list_window)
router = Router()
router.include_router(dialog)
