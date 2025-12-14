from aiogram.enums import ContentType
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment

from db.models import Campaign, Participation
from utils.role import Role


async def campaign_getter(dialog_manager: DialogManager, **kwargs):
    campaign_id = dialog_manager.start_data.get("campaign_id")
    participation_id = dialog_manager.start_data.get("participation_id")

    campaign = await Campaign.get(id=campaign_id)
    participation: Participation = await Participation.get(id=participation_id)

    icon = None
    if object_name := campaign.icon:
        icon = MediaAttachment(type=ContentType.PHOTO, path=f"minio://campaign-icons:{object_name}")

    return {
        "title": campaign.title,
        "description": campaign.description or "Описание отсутствует",
        "icon": icon,
        "is_owner": participation.role == Role.OWNER,
    }
