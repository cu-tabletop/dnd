import logging

from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Cancel
from aiogram_dialog.widgets.text import Const, Format

from db.models import Invitation, Participation
from services.settings import settings
from states.academy_campaigns import AcademyCampaignPreview
from states.invitation import InvitationAccept

logger = logging.getLogger(__name__)
router = Router()


async def invitation_getter(dialog_manager: DialogManager, **kwargs):
    if "invite" not in dialog_manager.dialog_data and isinstance(dialog_manager.start_data, dict):
        invite_id = dialog_manager.start_data.get("invitation_id")
        if not invite_id:
            msg = "Invitation ID is not specified"
            raise ValueError(msg)

        dialog_manager.dialog_data["invite_id"] = invite_id

    invite_id = dialog_manager.dialog_data["invite_id"]
    invitation = await Invitation.get_or_none(id=invite_id).prefetch_related("campaign")

    if invitation is None:
        msg = "Invitation not found"
        raise ValueError(msg)

    return {
        "campaign_title": invitation.campaign.title,
        "role": invitation.role.name,
    }


async def on_accept(c: CallbackQuery, b: Button, m: DialogManager):
    if "invite" not in m.dialog_data and isinstance(m.start_data, dict):
        invite_id = m.start_data.get("invitation_id")
        if not invite_id:
            msg = "Invitation ID is not specified"
            raise ValueError(msg)

        m.dialog_data["invite_id"] = invite_id

    invite_id = m.dialog_data["invite_id"]
    invitation = await Invitation.get_or_none(id=invite_id).prefetch_related("campaign", "created_by")

    if invitation is None:
        msg = "Invitation not found"
        raise ValueError(msg)

    user = m.middleware_data["user"]
    created_by = invitation.created_by

    participation = await Participation.create(user=user, campaign=invitation.campaign, role=invitation.role)
    await c.answer(f"Приглашение в кампанию {invitation.campaign.title} принято!")

    if created_by is not None:
        if settings.admin_bot is None:
            msg = "bot is not specified"
            raise TypeError(msg)
        await settings.admin_bot.send_message(
            created_by.id, f"ℹ️ @{user.username} (Игрок) принял приглашение в {invitation.campaign.title}"
        )

    await m.done()
    if invitation.campaign.verified:
        await m.start(
            AcademyCampaignPreview.preview,
            data={"campaign_id": invitation.campaign.id, "participation_id": participation.id},
        )
    else:
        # TODO @pxc1984: когда доделаем другие игры следует сюда добавить логику активации игры для них
        #   https://github.com/cu-tabletop/dnd/issues/10
        ...


router.include_router(
    Dialog(
        Window(
            Format("Вас пригласили в кампанию <b>{campaign_title}</b> на роль <b>{role}</b>"),
            Button(Const("Присоединиться"), id="accept", on_click=on_accept),
            Cancel(Const("Отказаться")),
            getter=invitation_getter,
            state=InvitationAccept.invitation,
        )
    )
)
