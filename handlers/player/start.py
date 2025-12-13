import logging

from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Column
from aiogram_dialog.widgets.text import Const

from db.models import Invitation, User
from db.models.participation import Participation
from handlers.player.upload import UploadCharacterRequest
from states.academy import Academy
from states.inventory_view import TargetType
from states.invitation import InvitationAccept
from states.other_games import OtherGames
from states.start_simple import StartSimple
from states.upload_character import UploadCharacter
from utils.redirect import redirect
from utils.uuid import is_valid_uuid

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart(deep_link=True))
async def start_args(message: Message, command: CommandObject, dialog_manager: DialogManager, user: User):
    if not command.args:
        return

    if not is_valid_uuid(command.args):
        logger.warning("User %s used /start with invalid UUID: %s", user.id, command.args)
        await message.reply(
            "❌ Неверная ссылка приглашения.\n\nПожалуйста, убедитесь, что ссылка скопирована полностью и корректно."
        )
        return

    invite = await Invitation.get_or_none(start_data=command.args).prefetch_related("user", "campaign")
    if not invite:
        logger.warning(
            "User %s used /start with arguments %s that weren't in the invitations",
            user.id,
            command.args,
        )
        await message.reply(
            "❌ Приглашение не найдено.\n\n"
            "Возможно, ссылка устарела или была отозвана. "
            "Попросите мастера отправить новое приглашение."
        )
        return

    await dialog_manager.reset_stack()

    if invite.user is None:
        invite.user = user
        await invite.save()
    elif invite.user.id != user.id:
        logger.warning(
            "User %s used /start with arguments %s that wasn't for him. It was for %s",
            user.id,
            command.args,
            invite.user.id,
        )
        await message.reply(
            "🔒 Это приглашение предназначено другому пользователю.\n\n"
            "Каждое приглашение привязано к конкретному Telegram-аккаунту. "
            "Попросите мастера отправить вам персональное приглашение."
        )
        return

    logger.info("%s пригласили в игру %s на роль %s", invite.user.id, invite.campaign.id, invite.role.name)
    if invite.used:
        await message.reply(
            "⚠️ Это приглашение уже было использовано.\n\n"
            "Если вы хотите присоединиться к кампании, попросите мастера "
            "отправить вам новое приглашение."
        )
        return

    participation = await Participation.get_or_none(user=user, campaign=invite.campaign)
    if participation is not None:
        logger.info(
            "User %s used /start in the %s campaign, where he was already invited. It was for %s.",
            user.id,
            command.args,
            invite.user.id,
        )
        await message.reply(
            f"🗳️ Вы уже участвуете в этой кампании в качестве {'игрока' if (i := participation.role == 0) else str(i)}"
        )
        return

    logger.debug(
        "Такой инвайт был найден. %s пригласили в игру %s на роль %s",
        invite.user.id,
        invite.campaign.id,
        invite.role.name,
    )

    invite.used = True
    await invite.save()

    await dialog_manager.start(InvitationAccept.invitation, data={"invitation_id": invite.id})


@router.message(CommandStart(deep_link=False))
async def start_simple(message: Message, dialog_manager: DialogManager, user: User):
    await dialog_manager.start(StartSimple.simple)


async def on_academy(c: CallbackQuery, b: Button, m: DialogManager):
    user: User = m.middleware_data["user"]
    if user.data is None:
        await m.start(
            UploadCharacter.upload,
            data={"request": UploadCharacterRequest(target_type=TargetType.USER, target_id=user.id)},
        )
        return
    await m.start(Academy.main)


async def on_other(c: CallbackQuery, b: Button, m: DialogManager):
    await m.start(OtherGames.main)


router.include_router(
    Dialog(
        Window(
            Const("Обычный /start"),
            Column(
                Button(Const("Академия"), id="academy", on_click=on_academy),
                Button(Const("Другие игры"), id="other_games", on_click=on_other),
                # TODO (@pxc1984): Добавить ближайшие встречи
                #    https://github.com/cu-tabletop/dnd/issues/11
            ),
            state=StartSimple.simple,
        ),
        on_start=redirect,
    )
)
