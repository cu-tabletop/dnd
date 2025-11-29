import logging
from aiogram import Router
from aiogram_dialog import Dialog, Window, SubManager
from aiogram_dialog.widgets.kbd import Button, SwitchTo
from aiogram_dialog.widgets.text import Const
from aiogram.types import CallbackQuery

import states.states as states

logger = logging.getLogger(__name__)


# === Гетеры ===


# === Кнопки ===
async def on_click_campaign_list(
    callback: CallbackQuery, button: Button, manager: SubManager
):
    await callback.answer("Приходите завтра.")


# === Окна ===
campaign_list_window = Window(
    Const("Привет"),
    SwitchTo(Const("Персонажи"), "switch_to_character_list", states.CharacterList.main),
    Button(Const("Кампейны"), "switch_to_campaign_list", on_click_campaign_list),
    Button(Const("Рейтинг"), "switch_to_rating", on_click_campaign_list),
    SwitchTo(
        Const("Архив_уведомлений"), "switch_to_notification", states.Notifications.main
    ),
    state=states.MainMenu.main,
    # getter=get_campaigns_data,
)

# === Создание диалога и роутера ===
dialog = Dialog(campaign_list_window)
router = Router()
router.include_router(dialog)
