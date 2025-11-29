import logging
from aiogram import Router
from aiogram_dialog import Dialog, Window, DialogManager, SubManager
from aiogram_dialog.widgets.kbd import Cancel
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram.types import CallbackQuery

from services.api_client import api_client
import states.states as states

logger = logging.getLogger(__name__)


# === Гетеры ===

# === Кнопки ===

# === Окна ===
campaign_list_window = Window(
    Cancel(Const("пока")),
    state=states.CampaignList.main,
    # getter=get_campaigns_data,
)

# === Создание диалога и роутера ===
dialog = Dialog(campaign_list_window)
router = Router()
router.include_router(dialog)
