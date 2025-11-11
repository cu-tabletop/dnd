from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Cancel
from aiogram_dialog.widgets.text import Const

from states.add_admin import AddAdminStates
from states.campaign_interaction import CampaignInteractionStates
from .start_menu import CAMPAIGNS

router = Router()


async def on_add_admin(
    message: Message,
    callback: CallbackQuery,
    dialog_manager: DialogManager,
    text: str,
):
    dialog_manager.dialog_data["admin_id"] = text
    await callback.message.answer(
        f"В кампанию {CAMPAIGNS[0]['name']} добавлен ещё один ГМ"
    )
    await dialog_manager.start(CampaignInteractionStates.main)


async def get_data(dialog_manager: DialogManager, **kwargs):
    return {
        "campaign_name": CAMPAIGNS[0]["name"],
        "icon": CAMPAIGNS[0]["icon"],
    }


add_admin_dialog = Dialog(
    Window(
        Const("<b>Добавление гейм-мастера к кампании {campaign_name}</b>"),
        TextInput(id="admin_id_input", on_success=on_add_admin),
        Cancel(Const("Отмена")),
        state=AddAdminStates.main,
        getter=get_data,
    )
)

router.include_router(add_admin_dialog)
