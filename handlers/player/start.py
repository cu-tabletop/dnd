import logging
import uuid

import tortoise.exceptions
from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager

from db.models import Invite, User

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart(deep_link=True))
async def start_args(message: Message, command: CommandObject, dialog_manager: DialogManager, user: User):
    try:
        invite = await Invite.get_or_none(start_data=command.args)
    except tortoise.exceptions.OperationalError as e:
        logger.warning(f"User {user.id} used /start with invalid UUID: {e}")
        return
    if not invite:
        logger.warning(
            f"User {user.id} used /start with arguments {command.args} that weren't in the invitations",
        )
        return
    if invite.user.id != user.id:
        logger.warning(
            f"User {user.id} used /start with arguments {command.args} that wasn't for him. It was for {invite.user.id}",
        )
        return
    await message.reply(
        f"Такой инвайт был найден. {invite.user.id} пригласили в игру {invite.campaign.id} на роль {invite.role.name}"
    )


@router.message(CommandStart(deep_link=False))
async def start_simple(message: Message, dialog_manager: DialogManager, user: User):
    await message.reply("обычный /start")
