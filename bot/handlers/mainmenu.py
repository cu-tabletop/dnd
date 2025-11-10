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
                # here go some of the companies
                Button(
                    Const("Назад"),
                    id="back_to_menu",
                    on_click=lambda c, b, m: m.switch_to(MainMenu.main),
                ),
            ),
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
