import logging

from aiogram import Router
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Column
from aiogram_dialog.widgets.text import Const

from states.mainmenu import MainMenu

router = Router()
logger = logging.getLogger(__name__)

router.include_router(
    Dialog(
        Window(
            Const("Это главное меню бота"),
            Column(
                Button(
                    Const("Кампании"), on_click=..., id="mainmenucampaigns"
                ),
                Button(
                    Const("Ваншоты"), on_click=..., id="mainmenucampaigns"
                ),
                Button(
                    Const("Академия"), on_click=..., id="mainmenucampaigns"
                ),
            ),
            state=MainMenu.main,
        )
    )
)
