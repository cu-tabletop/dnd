import logging
from typing import Any

from aiogram import Router
from aiogram.enums import ContentType
from aiogram.types import CallbackQuery
from aiogram_dialog import Data, Dialog, DialogManager, Window
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.kbd import Button, Cancel, Group
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from db.models.campaign import Campaign
from db.models.participation import Participation
from services.role import Role

from . import states

logger = logging.getLogger(__name__)


# === Гетеры ===
async def get_campaign_manage_data(dialog_manager: DialogManager, **kwargs):
    if "campaign_id" not in dialog_manager.dialog_data and isinstance(dialog_manager.start_data, dict):
        dialog_manager.dialog_data["campaign_id"] = dialog_manager.start_data["campaign_id"]
        dialog_manager.dialog_data["participation_id"] = dialog_manager.start_data["participation_id"]

    campaign_id = dialog_manager.dialog_data.get("campaign_id", 0)
    participation_id = dialog_manager.dialog_data.get("participation_id", 0)

    campaign: Campaign = await Campaign.get(id=campaign_id)
    participation: Participation = await Participation.get(id=participation_id)

    icon = None
    if file_id := campaign.icon:
        icon = MediaAttachment(type=ContentType.PHOTO, file_id=MediaId(file_id))

    return {
        "campaign_title": campaign.title,
        "campaign_description": campaign.description or "Описание отсутствует",
        "icon": icon,
        "is_owner": participation.role == Role.OWNER,
    }


# === Кнопки ===
async def on_edit_info(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    campaign_id = dialog_manager.dialog_data["campaign_id"]
    participation_id = dialog_manager.dialog_data["participation_id"]
    await dialog_manager.start(
        states.EditCampaignInfo.select_field,
        data={"campaign_id": campaign_id, "participation_id": participation_id},
    )


async def on_manage_characters(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    campaign_id = dialog_manager.dialog_data.get("campaign_id", {})
    await dialog_manager.start(
        states.ManageCharacters.character_menu,
        data={"campaign_id": campaign_id},
    )


async def on_permissions(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    campaign_id = dialog_manager.dialog_data.get("campaign_id", {})
    await dialog_manager.start(
        states.EditPermissions.main,
        data={"campaign_id": campaign_id},
    )


"""
async def on_stats(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    campaign_data = dialog_manager.dialog_data.get("selected_campaign", {})
    campaign = CampaignModelSchema(**campaign_data)
    stats_text = (
        f"📊 Статистика: {campaign.title}\n\n"
        f"👥 Количество студентов: 12\n"
        f"📚 Активных заданий: 5\n"
        f"⭐ Средний уровень: 4.2\n"
        f"🏆 Лучший студент: Гарри Поттер\n\n"
        f"📈 Прогресс: 78%"
    )
    await callback.answer(stats_text, show_alert=True)
"""

# === Окна ===
campaign_manage_window = Window(
    DynamicMedia("icon"),
    Format("🎓 Управление: {campaign_title}\n\nОписание: {campaign_description}\nВыберите действие:"),
    Group(
        Button(
            Const("🤝 Встречи"),
            id="meetings",
        ),
        Button(
            Const("✏️ Управление кампанией"),
            id="edit_info",
            on_click=on_edit_info,
        ),
        Button(
            Const("👥 Управление персонажами"),
            id="manage_characters",
            on_click=on_manage_characters,
        ),
        Button(
            Const("🧙‍♂️ Управление мастерами"),
            id="permissions",
            on_click=on_permissions,
            when="is_owner",
        ),
        width=1,
    ),
    Cancel(Const("⬅️ Назад")),
    state=states.CampaignManage.main,
    getter=get_campaign_manage_data,
)


# === Создание диалога и роутера ===
async def close_on_deleted(start_data: Data, result: Any, dialog_manager: DialogManager, **kwargs):
    if isinstance(result, dict) and result.get("deleted", False):
        await dialog_manager.done()


dialog = Dialog(campaign_manage_window, on_process_result=close_on_deleted)
router = Router()
router.include_router(dialog)
