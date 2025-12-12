import logging

from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from db.models import Invitation, Participation, User
from utils.uuid import is_valid_uuid

from . import states

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
        await message.reply(f"🗳️ Вы уже участвуете в этой кампании в качестве {participation.role}")
        return

    logger.debug(
        "Такой инвайт был найден. %s пригласили в игру %s на роль %s",
        invite.user.id,
        invite.campaign.id,
        invite.role.name,
    )

    invite.used = True
    await invite.save()

    await dialog_manager.start(
        states.InviteMenu.invite,
        data={"invitation_id": invite.id, "campaign_id": invite.campaign.id},
    )


@router.message(CommandStart(deep_link=False))
async def cmd_start(message: Message, dialog_manager: DialogManager):
    user: User = dialog_manager.middleware_data["user"]

    welcome_text = (
        f"👋 Добро пожаловать, {user.username or 'путник'}!\n\n"
        "Я бот для организации настольных ролевых игр.\n"
        "Здесь вы можете:\n"
        "• Создавать кампании 🏰\n"
        "• Управлять персонажами 👥\n"
        "• Приглашать друзей в приключения ✨\n\n"
        "Давайте начнем ваше приключение!"
    )

    await message.answer(welcome_text)

    await dialog_manager.start(
        state=states.CampaignList.main,
        mode=StartMode.RESET_STACK,
    )
