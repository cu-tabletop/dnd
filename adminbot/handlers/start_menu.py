from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Column
from aiogram_dialog.widgets.text import Const

from settings import settings
from states.create_campaign import CampaignCreate
from states.mainmenu import MainMenuStates

router = Router()

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


def get_campaigns_keyboard():
    buttons = []
    for campaign in CAMPAIGNS:
        buttons.append(
            Button(
                Const(f"{campaign['name']}"),
                id=str(campaign["id"]),
                on_click=on_select_campaign,
            )
        )
    return Column(*buttons)


@router.message(Command(commands=["start", "menu"]))
async def cmd_main_menu(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(MainMenuStates.main)


start_menu_dialog = Dialog(
    Window(
        Const("<b>Главное меню DnD бота</b>\n\nВыберите кампанию:"),
        Button(
            Const("Cоздать новую кампанию"),
            id="create_campaign",
            on_click=on_create_campaign,
        ),
        Const("\nСуществующие кампании:"),
        get_campaigns_keyboard(),
        state=MainMenuStates.main,
    ),
)

router.include_router(start_menu_dialog)
