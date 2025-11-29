import json
import logging
from aiogram import Router
from aiogram.enums import content_type
from aiogram_dialog import Dialog, Window, DialogManager, SubManager
from aiogram_dialog.widgets.kbd import Button, Cancel
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram_dialog.widgets.link_preview import LinkPreview
from aiogram.types import CallbackQuery, Message

from services.api_client import api_client
import states.states as states

logger = logging.getLogger(__name__)


# === Гетеры ===
async def get_campaigns_data(dialog_manager: DialogManager, **kwargs):
    user_id = dialog_manager.start_data.get("user_id")
    page = dialog_manager.dialog_data.get("page", 0)
    campaigns_per_page = 5

    campaigns = await api_client.get_campaigns(user_id=user_id)

    logger.debug(f"Полученные компейны: {campaigns}")

    if not campaigns:
        return {
            "campaigns": [],
            "current_page": 1,
            "total_pages": 1,
            "has_prev": False,
            "has_next": False,
            "has_campaigns": False,
        }

    start_idx = page * campaigns_per_page
    end_idx = start_idx + campaigns_per_page
    current_campaigns = campaigns[start_idx:end_idx]
    total_pages = (len(campaigns) + campaigns_per_page - 1) // campaigns_per_page

    return {
        "campaigns": current_campaigns,
        "current_page": page + 1,
        "total_pages": total_pages,
        "has_prev": page > 0,
        "has_next": end_idx < len(campaigns),
        "has_campaigns": len(campaigns) > 0,
    }


# === Кнопки ===
async def on_campaign_selected(
    callback: CallbackQuery, button: Button, manager: SubManager
):
    campaign_id = manager.item_id
    logger.info(f"Selected campaign ID: {campaign_id}")

    campaigns_data = await get_campaigns_data(manager)
    selected_campaign = next(
        (camp for camp in campaigns_data["campaigns"] if str(camp.id) == campaign_id),
        None,
    )

    if selected_campaign:
        manager.dialog_data["selected_campaign"] = selected_campaign.model_dump()

    await manager.start(
        campaign_states.CampaignManage.main,
        data={"selected_campaign": selected_campaign.model_dump()},
    )


async def on_character_load(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
):
    if message.document and message.document.file_name.endswith(".json"):
        try:
            # Берем фото максимального качества
            doc = message.document

            file = await message.bot.get_file(doc.file_id)
            json_file = await message.bot.download(file)
            json_data = json_file.read().decode("utf-8")
            json_data = json.loads(json_file.read().decode("utf-8"))

            character = await api_client.create_character(
                message.from_user.id, json_data
            )

            await message.answer("Персонаж {character.name} успешно создан!")
            await dialog_manager.done(result={"selected_character": character})
        except Exception as e:
            logger.error(f"Error processing photo: {e}")
            await message.answer("❌ Ошибка при обработке персонажа")
    else:
        await message.answer(
            "❌ Пожалуйста, отправьте файл с персонажем в формате .json"
        )


# === Окна ===
campaign_list_window = Window(
    Const("Содайте персонажа на https://longstoryshort.app и загрузите .json здесь\n"),
    LinkPreview(is_disabled=True),
    MessageInput(on_character_load, content_type.ContentType.DOCUMENT),
    Cancel(Const("🔙 Отмена")),
    state=states.CrateCharacter.main,
    getter=get_campaigns_data,
)

# === Создание диалога и роутера ===
dialog = Dialog(campaign_list_window)
router = Router()
router.include_router(dialog)
