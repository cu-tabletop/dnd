import logging

from aiogram import Router
from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.input import ManagedTextInput, TextInput
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Next
from aiogram_dialog.widgets.link_preview import LinkPreview
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from db.models import Invitation, Participation
from db.models.campaign import Campaign
from db.models.user import User
from services.invitation import generate_link, generate_qr
from services.role import Role
from services.settings import settings
from states.academy_campaigns import AcademyCampaignPreview

from . import states

logger = logging.getLogger(__name__)


# === Гетеры ===
async def get_link(dialog_manager: DialogManager, **kwargs):
    created_by: User = dialog_manager.middleware_data["user"]

    if "link" not in dialog_manager.dialog_data and isinstance(dialog_manager.start_data, dict):
        campaign_id = dialog_manager.start_data.get("campaign_id", 0)
        role = dialog_manager.start_data.get("role", Role.PLAYER)

        dialog_manager.dialog_data["invite_data"] = {
            "campaign_id": campaign_id,
            "created_by_id": created_by.id,
            "role": role.value if hasattr(role, "value") else role,
        }

        campaign = await Campaign.get(id=campaign_id)
        invite = await Invitation.create(campaign=campaign, role=role, created_by=created_by)

        link: str = await generate_link(invite)
        dialog_manager.dialog_data["link"] = link
        dialog_manager.dialog_data["invite_id"] = invite.id

    return {"link": link}


async def get_qr(dialog_manager: DialogManager, **kwargs):
    link = dialog_manager.dialog_data["link"]
    path = await generate_qr(link)
    qr_img = MediaAttachment(ContentType.PHOTO, path=path)
    return {"qr": qr_img}


async def invitation_getter(dialog_manager: DialogManager, **kwargs):
    if "invite" not in dialog_manager.dialog_data and isinstance(dialog_manager.start_data, dict):
        invite_id = dialog_manager.start_data.get("invitation_id")
        if not invite_id:
            msg = "Invitation ID is not specified"
            raise ValueError(msg)

        dialog_manager.dialog_data["invite_id"] = invite_id

    invite_id = dialog_manager.dialog_data["invite_id"]
    invite = await Invitation.get_or_none(id=invite_id).prefetch_related("campaign")

    if invite is None:
        msg = "Invitation not found"
        raise ValueError(msg)

    return {
        "campaign_title": invite.campaign.title,
        "role": invite.role.name,
    }


# === Кнопки ===
async def on_regenerate_link(mes: CallbackQuery, wid: Button, dialog_manager: DialogManager):
    invite_data = dialog_manager.dialog_data["invite_data"]
    campaign = await Campaign.get(id=invite_data["campaign_id"])
    created_by = await User.get(id=invite_data["created_by_id"])
    role = invite_data["role"]

    new_invitation = await Invitation.create(campaign=campaign, role=role, created_by=created_by)
    new_link = await generate_link(new_invitation)

    dialog_manager.dialog_data["link"] = new_link
    dialog_manager.dialog_data["invite_id"] = new_invitation.id

    await mes.answer("✅ Сгенерирована новая ссылка")


async def on_username_entered(
    mes: Message,
    wid: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str,
):
    username = text.lstrip("@")

    user = await User.get_or_none(username=username)

    if user is None:
        await mes.answer(f"❌ Пользователь @{username} не найден")
        return

    invite_id = dialog_manager.dialog_data.get("invite_id")
    if not invite_id:
        await mes.answer("❌ Приглашение не найдено")
        return

    invitation = await Invitation.get_or_none(id=invite_id)
    if invitation is None:
        await mes.answer("❌ Приглашение не найдено")
        return

    invitation.user = user
    await invitation.save()

    bot = settings.player_bot if invitation.role == Role.PLAYER else settings.admin_bot

    if bot is None:
        msg = "bot is not specified"
        raise TypeError(msg)

    link = dialog_manager.dialog_data["link"]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="ℹ️ Посмотреть приглашение", url=link)]])

    await bot.send_message(chat_id=user.id, text="Вам пришло приглашение", reply_markup=keyboard)

    await mes.answer("✅ Успешно отправлено!")
    await dialog_manager.done()


async def on_accept(c: CallbackQuery, b: Button, m: DialogManager):
    invite_id = m.dialog_data.get("invite_id")
    if not invite_id:
        await c.answer("❌ Приглашение не найдено", show_alert=True)
        await m.reset_stack()
        return

    invite = await Invitation.get_or_none(id=invite_id).prefetch_related("campaign", "created_by")
    if invite is None:
        await c.answer("❌ Приглашение не найдено", show_alert=True)
        await m.reset_stack()
        return

    created_by = invite.created_by
    user = m.middleware_data["user"]
    participation = await Participation.create(user=user, campaign=invite.campaign, role=invite.role)

    await c.answer(f"Приглашение в кампанию {invite.campaign.title} принято!")

    if created_by is not None:
        if settings.admin_bot is None:
            msg = "bot is not specified"
            raise TypeError(msg)
        await settings.admin_bot.send_message(
            created_by.id, f"ℹ️ @{user.username} (Мастер) принял приглашение в {invite.campaign.title}"
        )

    await m.done()

    if invite.campaign.verified:
        await m.start(
            AcademyCampaignPreview.preview,
            data={"campaign_id": invite.campaign.id, "participation_id": participation.id},
        )
    else:
        # TODO @pxc1984: когда доделаем другие игры следует сюда добавить логику активации игры для них
        #   https://github.com/cu-tabletop/dnd/issues/10
        pass


# === Окна ===
invite_menu_window = Window(
    Format(
        "Отправьте эту ссылку для приглашения: <code>{link}</code>\n"
        "Или напишите @username гостя здесь\n"
        "(учтите 1 ссылка – 1 приглашение)"
    ),
    LinkPreview(is_disabled=False),
    Button(Const("Сгенерировать новую ссылку"), id="regenerate_link", on_click=on_regenerate_link),
    TextInput(
        id="username_input",
        on_success=on_username_entered,
    ),
    Next(Const("📱 Сгенерировать QR-код")),
    Cancel(Const("⬅️ Назад")),
    state=states.InviteMenu.main,
    getter=get_link,
)


qr_window = Window(
    DynamicMedia("qr"),
    Back(Const("⬅️ Назад")),
    state=states.InviteMenu.view_qr,
    getter=get_qr,
)


invite_window = Window(
    Format("Вас пригласили в кампанию <b>{campaign_title}</b> на роль <b>{role}</b>"),
    Button(Const("Присоединиться"), id="accept_admin", on_click=on_accept),
    Cancel(Const("Отказаться")),
    getter=invitation_getter,
    state=states.InviteMenu.invite,
)


# === Создание диалога и роутера ===
dialog = Dialog(invite_menu_window, qr_window, invite_window)
router = Router()
router.include_router(dialog)
