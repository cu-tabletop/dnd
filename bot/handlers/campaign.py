import json
import logging

from aiogram import Router
from aiogram.enums import ContentType
from aiogram.types import User, Message
from aiogram_dialog import DialogManager, Dialog, Window
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Row
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Format, Const
from httpx import AsyncClient

from services.character import parse_character_data, CharacterData
from settings import settings
from states.campaign import CampaignDialog

router = Router()
logger = logging.getLogger(__name__)

PREVIEW_LENGTH = 200


async def char_getter(
    dialog_manager: DialogManager, event_from_user: User, **kwargs
) -> dict:
    ret = {}
    campaign_id = dialog_manager.start_data["campaign_id"]
    async with AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{settings.BACKEND_URL}/api/campaign/{campaign_id}/player/{event_from_user.id}/characters/get/"
        )
        if response.status_code != 200:
            ret["to_import"] = True
            ret["preview_available"] = False
            return ret

        response_data = response.json()
        ret["to_import"] = False
        ret["preview_available"] = True

        data = response_data["data"]
        character_data = json.loads(data["data"])
        ret["chardata"] = character_data

        info: CharacterData = parse_character_data(character_data)
        ret["chardata_preview"] = info.preview()
        ret["stats_preview"] = info.preview_stats()
        avatar_url = character_data.get("avatar", {}).get("webp")

        avatar = None
        if avatar_url:
            avatar = MediaAttachment(
                url=avatar_url,
                type=ContentType.PHOTO,
            )
        ret["avatar"] = avatar
    return ret


async def on_upload(
    message: Message, widget: MessageInput, dialog_manager: DialogManager
):
    if not message.document.file_name.endswith(".json"):
        await message.answer("Отправь .json!")
        return

    f = await message.bot.download(message.document.file_id)
    content = f.read()

    try:
        data = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError or UnicodeDecodeError:
        await message.answer("Это не json, проверь еще раз")
        return

    async with AsyncClient(timeout=30.0) as client:
        response = await client.put(
            f"{settings.BACKEND_URL}/api/character/put/",
            json={
                "owner_telegram_id": message.from_user.id,
                "campaign_id": dialog_manager.start_data["campaign_id"],
                "data": data,
            },
        )
        if response.status_code != 201 and response.status_code != 200:
            await message.answer(
                "Не получилось загрузить персонажа, попробуй еще раз"
            )
            return
        await message.answer("Успешно загружено")
        await dialog_manager.switch_to(CampaignDialog.preview)


router.include_router(
    Dialog(
        Window(
            Const("Импорт вашего персонажа", when="to_import"),
            DynamicMedia("avatar", when="avatar"),
            Format(
                "{chardata_preview}",
                when="preview_available",
            ),
            Button(
                Const("Загрузить .json из LSH"),
                id="to_upload_character",
                on_click=lambda c, b, m: m.switch_to(CampaignDialog.upload),
            ),
            Row(
                Button(
                    Const("Характеристики"),
                    id="stats",
                    on_click=lambda c, b, m: m.switch_to(CampaignDialog.stats),
                ),
                Button(
                    Const("Инвентарь"),
                    id="inventory",
                    on_click=lambda c, b, m: c.answer("TODO"),
                ),
            ),
            Cancel(Const("Назад")),
            getter=char_getter,
            state=CampaignDialog.preview,
        ),
        Window(
            Const("Отправь мне .json файл с своим персонажем"),
            Cancel(Const("Назад")),
            MessageInput(
                content_types=ContentType.DOCUMENT,
                id="upload_character",
                func=on_upload,
            ),
            state=CampaignDialog.upload,
        ),
        Window(
            Format("{stats_preview}"),
            Button(
                Const("Назад"),
                on_click=lambda c, b, m: m.switch_to(CampaignDialog.preview),
                id="back",
            ),
            getter=char_getter,
            state=CampaignDialog.stats,
        ),
    )
)
