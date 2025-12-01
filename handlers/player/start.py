import logging

import tortoise.exceptions
from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, Dialog, Window
from aiogram_dialog.widgets.kbd import Column, Button
from aiogram_dialog.widgets.text import Const

from db.models import Invite, User
from states.start_simple import StartSimple
from states.upload_character import UploadCharacter

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
    await dialog_manager.start(StartSimple.simple)


async def on_academy(c: CallbackQuery, b: Button, m: DialogManager):
    user: User = m.middleware_data["user"]
    if user.data is None:
        await m.start(UploadCharacter.upload, data={"source": "user"})
        return
    await c.answer("Да, вы участвуете в академии")


async def on_other(c: CallbackQuery, b: Button, m: DialogManager): ...


router.include_router(
    Dialog(
        Window(
            Const("Обычный /start"),
            Column(
                Button(Const("Академия"), id="academy", on_click=on_academy),
                Button(Const("Другие игры"), id="other_games", on_click=on_other),
                # Button(Const("Ближайшие встречи"), id="meetings", on_click=...),
            ),
            state=StartSimple.simple,
        )
    )
)
