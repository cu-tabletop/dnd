import logging

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager

from db.models import Invitation, Participation, User
from utils.invitation import get_invite_id

from .settings import settings

logger = logging.getLogger(__name__)


async def invitation_getter(dialog_manager: DialogManager, **kwargs):
    invite = await Invitation.get_or_none(id=get_invite_id(dialog_manager)).prefetch_related("campaign")

    if invite is None:
        msg = "Invitation not found"
        raise ValueError(msg)

    return {
        "campaign_title": invite.campaign.title,
        "role": invite.role.name,
    }


async def handle_accept_invitation(m: DialogManager, callback: CallbackQuery, user: User, invitation: Invitation):
    participation, _created = await Participation.get_or_create(
        user=user, campaign=invitation.campaign, role=invitation.role
    )

    await callback.answer(f"Приглашение в кампанию {invitation.campaign.title} принято!")

    if invitation.created_by is not None:
        if settings.admin_bot is None:
            msg = "bot is not specified"
            raise TypeError(msg)
        await settings.admin_bot.send_message(
            invitation.created_by.id, f"ℹ️ @{user.username} (Игрок) принял приглашение в {invitation.campaign.title}"
        )

    await m.done()

    return participation
