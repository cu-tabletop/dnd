import json
import logging
from aiogram import Router
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram.enums import ContentType
from aiogram_dialog.widgets.kbd import Button, Group, Cancel
from aiogram_dialog.widgets.text import Const, Format
from aiogram.types import CallbackQuery

from services.models import CampaignModelSchema
from . import states as campaign_states

logger = logging.getLogger(__name__)


# === Гетеры ===
async def get_campaign_manage_data(dialog_manager: DialogManager, **kwargs):
    if "selected_campaign" not in dialog_manager.dialog_data:
        campaign_data = dialog_manager.start_data.get("selected_campaign", {})
        dialog_manager.dialog_data["selected_campaign"] = campaign_data

    campaign = CampaignModelSchema(
        **dialog_manager.dialog_data["selected_campaign"]
    )

    icon = None
    if campaign.icon:
        icon = MediaAttachment(
            type=ContentType.PHOTO,
            file_id=MediaId(campaign.icon),
        )

    return {
        "campaign_title": campaign.title,
        "campaign_description": campaign.description or "Описание отсутствует",
        "icon": icon,
    }


async def update_data(_, result, dialog_manager: DialogManager, **kwargs):
    logger.debug(f"Результат: {result}")
    dialog_manager.dialog_data["selected_campaign"].update(
        result["update_data"]
    )


# === Кнопки ===
async def on_edit_info(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    selected_campaign = dialog_manager.dialog_data.get("selected_campaign", {})
    await dialog_manager.start(
        campaign_states.EditCampaignInfo.select_field,
        data={"selected_campaign": selected_campaign},
    )


async def on_manage_characters(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    selected_campaign = dialog_manager.dialog_data.get("selected_campaign", {})
    await dialog_manager.start(
        campaign_states.ManageCharacters.character_selection,
        data={"selected_campaign": selected_campaign},
    )


async def on_permissions(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    selected_campaign = dialog_manager.dialog_data.get("selected_campaign", {})
    await dialog_manager.start(
        campaign_states.EditPermissions.main,
        data={"selected_campaign": selected_campaign},
    )


# async def on_stats(
#     callback: CallbackQuery, button: Button, dialog_manager: DialogManager
# ):
#     campaign_data = dialog_manager.dialog_data.get("selected_campaign", {})
#     campaign = CampaignModelSchema(**campaign_data)
#     stats_text = (
#         f"📊 Статистика группы: {campaign.title}\n\n"
#         f"👥 Количество студентов: 12\n"
#         f"📚 Активных заданий: 5\n"
#         f"⭐ Средний уровень: 4.2\n"
#         f"🏆 Лучший студент: Гарри Поттер\n\n"
#         f"📈 Прогресс группы: 78%"
#     )
#     await callback.answer(stats_text, show_alert=True)


# === Окна ===
campaign_manage_window = Window(
    DynamicMedia("icon"),
    Format(
        "🎓 Управление группой: {campaign_title}\n\n"
        "Описание: {campaign_description}\n"
        "Выберите действие:"
    ),
    Group(
        Button(
            Const("✏️ Редактировать информацию"),
            id="edit_info",
            on_click=on_edit_info,
        ),
        Button(
            Const("👥 Управление персонажами"),
            id="manage_characters",
            on_click=on_manage_characters,
        ),
        # Button(
        #     Const("🧙‍♂️ Управление мастерами"),
        #     id="permissions",
        #     on_click=on_permissions,
        # ),
        width=1,
    ),
    Cancel(Const("⬅️ Назад к списку")),
    state=campaign_states.CampaignManage.main,
    getter=get_campaign_manage_data,
)

# === Создание диалога и роутера ===
dialog = Dialog(campaign_manage_window, on_process_result=update_data)
router = Router()
router.include_router(dialog)
