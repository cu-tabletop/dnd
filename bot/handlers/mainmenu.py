import logging
from aiogram import Router
from aiogram.types import User, CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Column, Select
from aiogram_dialog.widgets.text import Const, Format
from httpx import AsyncClient, HTTPStatusError
from typing import Optional, List

from settings import settings
from states.mainmenu import MainMenu


async def get_user_campaigns(telegram_id: int) -> Optional[List[dict]]:
    try:
        async with AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{settings.BACKEND_URL}/api/campaign/get/",
                params={"user_id": telegram_id},
            )
            response.raise_for_status()

            data = response.json()

            logger.debug(
                "Backend returned the following campaigns data: %s", data
            )

            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            else:
                logger.warning(f"Unexpected response format: {data}")
                return []

    except HTTPStatusError as e:
        logger.error(
            f"HTTP error fetching campaigns for user {telegram_id}: {e}"
        )
        return None
    except Exception as e:
        logger.error(
            f"Unexpected error fetching campaigns for user {telegram_id}: {e}"
        )
        return None


async def campaigns_list_getter(
    dialog_manager: DialogManager, **kwargs
) -> dict:
    user: User = dialog_manager.middleware_data["event_from_user"]
    telegram_id = user.id

    campaigns = await get_user_campaigns(telegram_id)

    return {
        "campaigns": campaigns or [],
        "has_campaigns": bool(campaigns),
        "user_id": telegram_id,
    }


def campaign_button_getter(campaign: dict) -> Button:
    campaign_id = campaign.get("id")
    title = campaign.get("title", "Unnamed Campaign")
    description = campaign.get("description", "")

    display_title = title[:30] + "..." if len(title) > 30 else title

    return Button(
        Format(f"{display_title}"),
        id=f"campaign_{campaign_id}",
        on_click=lambda c, b, m, camp_id=campaign_id: on_campaign_click(
            c, b, m, camp_id
        ),
    )


async def on_campaign_click(
    callback: CallbackQuery, button, manager: DialogManager, campaign_id: int
):
    logger.info(
        f"Campaign {campaign_id} clicked by user {manager.middleware_data['event_from_user'].id}"
    )
    await callback.answer(f"Campaign {campaign_id} selected!")


async def campaigns_detailed_getter(
    dialog_manager: DialogManager, **kwargs
) -> dict:
    user: User = dialog_manager.middleware_data["event_from_user"]
    telegram_id = user.id

    campaigns = await get_user_campaigns(telegram_id)

    dialog_manager.dialog_data["campaigns"] = campaigns or []

    display_campaigns = []
    for campaign in campaigns or []:
        display_campaigns.append(
            {
                "id": campaign.get("id"),
                "title": campaign.get("title", "Unnamed Campaign"),
                "description": campaign.get("description", ""),
                "display_title": f"{campaign.get('title', 'Unnamed Campaign')}"[
                    :35
                ]
                + "..."
                if len(campaign.get("title", "")) > 35
                else f"{campaign.get('title', 'Unnamed Campaign')}",
            }
        )

    return {
        "campaigns": display_campaigns,
        "has_campaigns": bool(campaigns),
        "no_campaigns_text": "У вас пока нет доступных кампаний"
        if not campaigns
        else "",
        "user_id": telegram_id,
    }


async def on_campaign_selected(
    callback: CallbackQuery, select, manager: DialogManager, item_id: str
): ...


router = Router()
logger = logging.getLogger(__name__)

campaigns_select = Select(
    Format("{item[title]}"),
    id="campaigns_select",
    item_id_getter=lambda item: str(item["id"]),
    items="campaigns",
    on_click=on_campaign_selected,
)

router.include_router(
    Dialog(
        Window(
            Const("Это главное меню бота"),
            Column(
                Button(
                    Const("Кампании"),
                    on_click=lambda c, b, m: m.switch_to(MainMenu.campaigns),
                    id="campaigns",
                ),
                Button(
                    Const("Ваншоты"),
                    on_click=lambda c, b, m: m.switch_to(MainMenu.oneshots),
                    id="oneshots",
                ),
                Button(
                    Const("Академия"),
                    on_click=lambda c, b, m: m.switch_to(MainMenu.academy),
                    id="academy",
                ),
            ),
            state=MainMenu.main,
        ),
        Window(
            Const("Это меню кампаний, к которым у вас есть доступ"),
            Column(
                campaigns_select,
                Button(
                    Const("Назад"),
                    id="back_to_menu",
                    on_click=lambda c, b, m: m.switch_to(MainMenu.main),
                ),
            ),
            getter=campaigns_list_getter,
            state=MainMenu.campaigns,
        ),
        Window(
            Const("Это меню ваншотов, к которым у вас есть доступ"),
            Column(
                # here go some of the companies
                Button(
                    Const("Назад"),
                    id="back_to_menu",
                    on_click=lambda c, b, m: m.switch_to(MainMenu.main),
                ),
            ),
            state=MainMenu.oneshots,
        ),
        Window(
            Const("Это меню АКАДЕМИИ!!"),
            Column(
                # here go some of the companies
                Button(
                    Const("Назад"),
                    id="back_to_menu",
                    on_click=lambda c, b, m: m.switch_to(MainMenu.main),
                ),
            ),
            state=MainMenu.academy,
        ),
    )
)
