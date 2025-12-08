import logging
import re
import tempfile
import uuid
from pathlib import Path

import qrcode
from aiogram import Bot

from db.models.invitation import Invitation
from services.role import Role

from .settings import settings

logger = logging.getLogger(__name__)


async def generate_link(invitation: Invitation) -> str:
    bot = settings.player_bot if invitation.role == Role.PLAYER else settings.admin_bot

    if isinstance(bot, Bot):
        bot_name = (await bot.get_me()).username
    else:
        msg = "bot is not specified"
        raise TypeError(msg)

    return f"https://t.me/{bot_name}?start={invitation.start_data}"


async def generate_qr(link: str) -> str:
    """Генерация QR-кода и возвращения пути к нему"""

    temp_dir = Path(tempfile.gettempdir()) / "bot_qr_codes"
    temp_dir.mkdir(parents=True, exist_ok=True)

    match = re.search(r"start=([a-f0-9\-]+)", link)
    filename = f"qr_{match.group(1)}.png" if match else f"qr_{uuid.uuid4()}.png"

    filepath = temp_dir / filename

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(link)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").get_image()
    img.save(filepath, format="PNG")

    return str(filepath)
