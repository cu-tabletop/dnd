import logging
from typing import List

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery, User
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Column, Select
from aiogram_dialog.widgets.text import Const, Format
from httpx import AsyncClient

from settings import settings
from states.create_campaign import CampaignCreate
from states.mainmenu import MainMenuStates

router = Router()
logger = logging.getLogger(__name__)

# ! Предполагается что мы будем фетчить кампании из ДБ
# ! Данный функционал ещё не реализован
CAMPAIGNS = [
    {
        "id": 1,
        "name": "Существующая кампания 1",
        "icon": settings.PATH_TO_DEFAULT_ICON,
    },
    {
        "id": 2,
        "name": "Существующая кампания 2",
        "icon": settings.PATH_TO_DEFAULT_ICON,
    },
]


async def on_create_campaign(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    await dialog_manager.start(CampaignCreate.name)


async def on_select_campaign(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    campaign_id = button.widget_id
    campaign_name = next(
        (c["name"] for c in CAMPAIGNS if str(c["id"]) == campaign_id),
        "Неизвестная",
    )
    await callback.answer(f"Выбрана кампания: {campaign_name}")


async def get_user_campaigns(telegram_id: int) -> List[dict]:
    async with AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{settings.BACKEND_URL}/api/campaign/get/",
            params={"user_id": telegram_id, "owned": True},
        )
        if response.status_code != 200:
            logger.warning("Backend returned non-200 code when fetching campaigns data")
            return []

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


async def on_campaign_selected(
    callback: CallbackQuery, select, manager: DialogManager, item_id: str
): ...


campaigns_select = Select(
    Format("{item[title]}"),
    id="campaigns_select",
    item_id_getter=lambda item: str(item["id"]),
    items="campaigns",
    on_click=on_campaign_selected,
)


@router.message(Command(commands=["start", "menu"]))
async def cmd_main_menu(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(MainMenuStates.main)


start_menu_dialog = Dialog(
    Window(
        Const("<b>Главное меню DnD бота</b>\n\nВыберите кампанию:"),
        Column(
            Button(
                Const("Cоздать новую кампанию"),
                id="create_campaign",
                on_click=on_create_campaign,
            ),
            campaigns_select,
        ),
        Const("\nСуществующие кампании:"),
        getter=campaigns_list_getter,
        state=MainMenuStates.main,
    ),
)

router.include_router(start_menu_dialog)
