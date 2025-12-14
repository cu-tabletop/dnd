import logging

from aiogram.enums import ContentType
from aiogram_dialog.api.entities import MediaAttachment

from db.models.base import CharacterData as BaseCharacterData
from utils.character import CharacterData, parse_character_data

logger = logging.getLogger(__name__)


async def update_char_data(holder: BaseCharacterData, data: dict):
    holder.data = data
    await holder.save()


def character_preview_getter(user: BaseCharacterData, data: dict):
    ret = {}
    info: CharacterData = parse_character_data(data)
    ret["character_data_preview"] = info.preview()
    avatar_url = data.get("avatar", {}).get("webp")
    if avatar_url:
        ret["avatar"] = MediaAttachment(
            url=avatar_url,
            type=ContentType.PHOTO,
        )
    else:
        logger.warning("No avatar for user %d", user.id)

    return ret
