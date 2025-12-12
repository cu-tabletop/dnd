import logging

from aiogram import Router
from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.input import ManagedTextInput, TextInput
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Next
from aiogram_dialog.widgets.link_preview import LinkPreview
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, Multi

from db.models import Invitation
from db.models.campaign import Campaign
from db.models.user import User
from services.invitation import handle_accept_invitation, invitation_getter
from services.settings import settings
from utils.invitation import generate_link, generate_qr
from utils.role import Role

from . import states

logger = logging.getLogger(__name__)


# === Гетеры ===
async def get_link(dialog_manager: DialogManager, **_):
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


async def get_qr(dialog_manager: DialogManager, **_):
    link = dialog_manager.dialog_data["link"]
    path = await generate_qr(link)
    qr_img = MediaAttachment(ContentType.PHOTO, path=path)
    return {"qr": qr_img}


# === Кнопки ===
async def on_regenerate_link(mes: CallbackQuery, _: Button, dialog_manager: DialogManager):
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
    _: ManagedTextInput,
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


async def on_accept(msg: CallbackQuery, _: Button, dialog_manager: DialogManager):
    invite_id = dialog_manager.dialog_data.get("invite_id")
    if not invite_id:
        await msg.answer("❌ Приглашение не найдено", show_alert=True)
        await dialog_manager.reset_stack()
        return

    invite = await Invitation.get_or_none(id=invite_id).prefetch_related("campaign", "created_by")
    if invite is None:
        await msg.answer("❌ Приглашение не найдено", show_alert=True)
        await dialog_manager.reset_stack()
        return

    user = dialog_manager.middleware_data["user"]

    participation = await handle_accept_invitation(dialog_manager, msg, user, invite)

    if invite.campaign.verified:
        await dialog_manager.start(
            states.CampaignList.main,
            data={
                "campaign_id": invite.campaign.id,
                "participation_id": participation.id,
                "redirect_to": states.CampaignManage.main,
            },
            mode=StartMode.RESET_STACK,
        )
    else:
        # TODO @pxc1984: когда доделаем другие игры следует сюда добавить логику активации игры для них
        #   https://github.com/cu-tabletop/dnd/issues/10
        pass


# === Окна ===
invite_menu_window = Window(
    Multi(
        Const("✉️ Приглашение в кампанию\n"),
        Format("\nСсылка для приглашения: <code>{link}</code>"),
        Const("\nИли введите @username пользователя ниже"),
        Const("(каждая ссылка работает только один раз)"),
        sep="\n",
    ),
    LinkPreview(is_disabled=False),
    Button(Const("🔄 Сгенерировать новую ссылку"), id="regenerate_link", on_click=on_regenerate_link),
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
    Format("🎉 Вас пригласили в кампанию!\n\n<b>{campaign_title}</b>\nРоль: <b>{role}</b>"),
    Button(Const("✅ Присоединиться"), id="accept_admin", on_click=on_accept),
    Cancel(Const("❌ Отказаться")),
    getter=invitation_getter,
    state=states.InviteMenu.invite,
)


# === Создание диалога и роутера ===
dialog = Dialog(invite_menu_window, qr_window, invite_window)
router = Router()
router.include_router(dialog)
