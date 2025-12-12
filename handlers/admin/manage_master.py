import logging
from uuid import UUID

from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import (
    Button,
    Cancel,
    ScrollingGroup,
    Select,
    SwitchTo,
)
from aiogram_dialog.widgets.text import Const, Format, Multi
from tortoise.exceptions import OperationalError

from db.models.campaign import Campaign
from db.models.participation import Participation
from services.settings import settings
from utils.role import Role

from . import states

logger = logging.getLogger(__name__)


# === ГЕТЕРЫ ===
async def get_permissions_data(dialog_manager: DialogManager, **kwargs):
    if "campaign_id" not in dialog_manager.dialog_data and isinstance(dialog_manager.start_data, dict):
        dialog_manager.dialog_data["campaign_id"] = dialog_manager.start_data.get("campaign_id", 0)
        dialog_manager.dialog_data["participation_id"] = dialog_manager.start_data.get("participation_id", 0)

    campaign = await Campaign.get(id=dialog_manager.dialog_data.get("campaign_id", 0))

    p_users: list[Participation] = await (
        Participation.filter(campaign=campaign, role=Role.MASTER).prefetch_related("user").all()
    )

    return {"users": p_users, "campaign": campaign}


async def get_user_permission_data(dialog_manager: DialogManager, **kwargs):
    participation_id = dialog_manager.dialog_data["selected_participation_id"]
    selected_participation = await Participation.get(id=participation_id).prefetch_related("user")
    user = selected_participation.user

    return {"username": user.username}


# === КНОПКИ ===
async def on_user_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    participation_id: UUID,
):
    dialog_manager.dialog_data["selected_participation_id"] = participation_id
    await dialog_manager.switch_to(states.EditPermissions.selected_master)


async def on_remove_user(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    participation_id = dialog_manager.dialog_data["selected_participation_id"]
    selected_participation = await Participation.get(id=participation_id).prefetch_related("user", "campaign")

    try:
        user = selected_participation.user
        campaign = selected_participation.campaign

        await selected_participation.delete()
        await callback.answer(
            f"✅ Пользователь {user.username} удален из группы",
            show_alert=True,
        )

        if settings.admin_bot is None:
            msg = "bot is not specified"
            raise TypeError(msg)
        await settings.admin_bot.send_message(user.id, f"👋 Вас удалили из {campaign.title}")

        await dialog_manager.switch_to(states.EditPermissions.main)
    except OperationalError as e:
        logger.exception("Error processing delete participation", exc_info=e)
        await callback.answer("❌ Ошибка при удалении", show_alert=True)


async def on_add_master(mes: CallbackQuery, wid: Button, dialog_manager: DialogManager):
    await dialog_manager.start(
        states.InviteMenu.main, data={"campaign_id": dialog_manager.dialog_data["campaign_id"], "role": Role.MASTER}
    )


# === Окна ===
permissions_main_window = Window(
    Multi(
        Format("👑 Управление мастерами: {campaign.title}\n"),
        Const("Мастера могут управлять персонажами в этой кампании"),
    ),
    ScrollingGroup(
        Select(
            Format("👤 {item.user.username}"),
            id="user_permission",
            items="users",
            item_id_getter=lambda item: item.id,
            on_click=on_user_selected,
            type_factory=UUID,
        ),
        hide_on_single_page=True,
        height=5,
        id="users_permissions_list",
    ),
    Button(
        Const("➕ Пригласить мастера"),
        id="invite_user",
        on_click=on_add_master,
    ),
    Cancel(Const("⬅️ Назад")),
    state=states.EditPermissions.main,
    getter=get_permissions_data,
)

select_permission_window = Window(
    Format("👤 Мастер: @{username}\n"),
    Const("\nВыберите действие:"),
    Button(Const("🚫 Удалить мастера"), id="remove_user", on_click=on_remove_user),
    SwitchTo(
        Const("⬅️ Назад к списку"),
        id="back",
        state=states.EditPermissions.main,
    ),
    state=states.EditPermissions.selected_master,
    getter=get_user_permission_data,
)


# === Создание диалога и роутера ===
permissions_dialog = Dialog(
    permissions_main_window,
    select_permission_window,
)

router = Router()
router.include_router(permissions_dialog)
