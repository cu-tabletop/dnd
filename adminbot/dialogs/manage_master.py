from aiogram import Router
from aiogram_dialog import Dialog, Window, DialogManager, SubManager
from aiogram_dialog.widgets.input.text import TextInput
from aiogram_dialog.widgets.kbd import (
    Button,
    SwitchTo,
    Cancel,
    ListGroup,
    Select,
)
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram.types import CallbackQuery, Message

from services.api_client import api_client
from . import states as campaign_states

# === ГЕТЕРЫ ===


async def get_permissions_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных о правах доступа к кампании"""
    campaign = dialog_manager.dialog_data.get("selected_campaign", {})
    campaign_id = campaign.get("id")

    # Заглушка данных о пользователях и их правах
    # В реальности будем получать из API
    mock_users = [
        {
            "id": 1,
            "name": "Альбус Дамблдор",
            "telegram_id": 123456789,
            "permission_level": 2,  # 0-участник, 1-редактор, 2-владелец
            "permission_text": "Владелец",
            "status": "активен",
            "join_date": "01.09.2023",
        },
        {
            "id": 2,
            "name": "Минерва Макгонагалл",
            "telegram_id": 987654321,
            "permission_level": 1,
            "permission_text": "Редактор",
            "status": "активен",
            "join_date": "01.09.2023",
        },
        {
            "id": 3,
            "name": "Северус Снейп",
            "telegram_id": 555555555,
            "permission_level": 0,
            "permission_text": "Участник",
            "status": "активен",
            "join_date": "01.09.2023",
        },
        {
            "id": 4,
            "name": "Долорес Амбридж",
            "telegram_id": 666666666,
            "permission_level": 0,
            "permission_text": "Участник",
            "status": "заблокирован",
            "join_date": "01.01.2024",
        },
    ]

    return {
        "users": mock_users,
        "campaign_title": campaign.get("title", "Группа"),
        "campaign_id": campaign_id,
        "total_users": len(mock_users),
        "active_users": len([u for u in mock_users if u["status"] == "активен"]),
    }


async def get_user_permission_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных о конкретном пользователе для изменения прав"""
    selected_user_id = dialog_manager.dialog_data.get("selected_user_id")
    users_data = await get_permissions_data(dialog_manager)

    # Ищем пользователя по telegram_id (так как в ListGroup используется telegram_id
    # как идентификатор)
    selected_user = next(
        (
            user
            for user in users_data["users"]
            if str(user["telegram_id"]) == str(selected_user_id)
        ),
        None,
    )

    permission_levels = [
        {
            "level": 0,
            "name": "Участник",
            "description": "Может просматривать и участвовать",
        },
        {"level": 1, "name": "Редактор", "description": "Может редактировать контент"},
        {
            "level": 2,
            "name": "Владелец",
            "description": "Полный доступ ко всем функциям",
        },
    ]

    return {
        "user": selected_user
        or {"name": "Неизвестный пользователь", "permission_text": "Нет прав"},
        "campaign_title": users_data["campaign_title"],
        "permission_levels": permission_levels,
        "current_level": selected_user["permission_level"] if selected_user else 0,
    }


# === КНОПКИ ===


async def on_user_selected(
    callback: CallbackQuery, widget: Select, dialog_manager: SubManager
):
    """Обработчик выбора пользователя для изменения прав"""
    dialog_manager.dialog_data["selected_user_id"] = dialog_manager.item_id
    await dialog_manager.switch_to(campaign_states.EditPermissions.select_permission)


async def on_permission_level_selected(
    callback: CallbackQuery, widget: Select, dialog_manager: SubManager
):
    """Обработчик выбора уровня прав"""
    selected_user_id = dialog_manager.dialog_data.get("selected_user_id")
    new_permission_level = int(dialog_manager.item_id)

    # Получаем данные о кампании и пользователе
    campaign = dialog_manager.dialog_data.get("selected_campaign", {})
    campaign_id = campaign.get("id")
    current_user_id = callback.from_user.id  # ID текущего пользователя (владельца)

    # Вызов API для изменения прав
    result = await api_client.edit_permissions(
        campaign_id=campaign_id,
        owner_id=current_user_id,
        user_id=int(selected_user_id),  # type: ignore
        status=new_permission_level,
    )

    if "error" in result:
        await callback.answer(f"❌ Ошибка: {result['error']}", show_alert=True)
    else:
        permission_names = {0: "Участник", 1: "Редактор", 2: "Владелец"}
        await callback.answer(
            f"✅ Права изменены на: {permission_names[new_permission_level]}",
            show_alert=True,
        )

    # Возвращаемся к списку пользователей
    await dialog_manager.switch_to(campaign_states.EditPermissions.main)


async def on_invite_user(
    message: Message,
    button: Button,
    dialog_manager: DialogManager,
    text: str,
):
    """Обработчик приглашения нового пользователя"""
    username = text.lstrip("@").strip()

    if not username:
        await message.answer("❌ Введите username пользователя")
        return

    # В реальном приложении здесь должен быть поиск пользователя
    # по username в вашей системе
    # Пока используем заглушку - создаем временного пользователя
    try:
        # Пытаемся получить ID пользователя (в реальности через API вашей системы)
        # Здесь заглушка - используем хэш от username как "ID"
        user_id = (await message.bot.get_chat(f"@{username}")).id

        campaign = dialog_manager.dialog_data.get("selected_campaign", {})
        campaign_id = campaign.get("id")
        owner_id = message.from_user.id

        # Добавляем пользователя через API
        result = await api_client.edit_permissions(
            campaign_id=campaign_id,
            owner_id=owner_id,
            user_id=user_id,
            status=0,  # Участник по умолчанию
        )

        if "error" in result:
            await message.answer(f"❌ Ошибка при приглашении: {result['error']}")
        else:
            await message.answer(f"✅ Пользователь @{username} приглашен в кампанию!")
            await dialog_manager.switch_to(
                campaign_states.EditPermissions.select_permission
            )

    except Exception:
        await message.answer(f"❌ Пользователь @{username} не найден.")


async def on_remove_user(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    """Обработчик удаления пользователя из кампании"""
    selected_user_id = dialog_manager.dialog_data.get("selected_user_id")

    if not selected_user_id:
        await callback.answer("❌ Сначала выберите пользователя", show_alert=True)
        return

    # Получаем данные о пользователе
    users_data = await get_permissions_data(dialog_manager)
    selected_user = next(
        (
            user
            for user in users_data["users"]
            if str(user["telegram_id"]) == str(selected_user_id)
        ),
        None,
    )

    if selected_user:
        campaign = dialog_manager.dialog_data.get("selected_campaign", {})
        campaign_id = campaign.get("id")
        owner_id = callback.from_user.id  # type: ignore

        # Вызов API для удаления пользователя
        # (установка прав в -1 или специальный статус)
        result = await api_client.edit_permissions(
            campaign_id=campaign_id,
            owner_id=owner_id,
            user_id=int(selected_user_id),
            status=-1,  # Специальный статус для удаления
        )

        if "error" in result:
            await callback.answer(
                f"❌ Ошибка при удалении: {result['error']}", show_alert=True
            )
        else:
            await callback.answer(
                f"✅ Пользователь {selected_user['name']} удален из группы",
                show_alert=True,
            )
            await dialog_manager.switch_to(campaign_states.EditPermissions.main)


# === ОКНА ===

# Главное окно управления правами доступа
permissions_main_window = Window(
    Multi(
        Format("🧙‍♂️ Управление мастерами: {campaign_title}\n\n"),
        Format("👥 Всего мастеров: {total_users}\n"),
        Format("🟢 Активных: {active_users}\n\n"),
        Const("Список пользователей и их прав:"),
    ),
    ListGroup(
        Button(
            Format(
                "👤 {item[name]} - {item[permission_text]}\n"
                "🟢 Статус: {item[status]}"
            ),
            id="user_permission",
            on_click=on_user_selected,  # type: ignore
        ),
        id="users_permissions_list",
        item_id_getter=lambda item: item["telegram_id"],
        items="users",
    ),
    SwitchTo(
        Const("➕ Пригласить мастера"),
        id="invite_user",
        state=campaign_states.EditPermissions.invite_master,
    ),
    Cancel(Const("⬅️ Назад")),
    state=campaign_states.EditPermissions.main,
    getter=get_permissions_data,
)

# Окно выбора уровня прав
select_permission_window = Window(
    Format(
        "🎯 Изменение прав доступа\n\n"
        "Мастер: {user[name]}\n"
        "Текущие права: {user[permission_text]}\n\n"
        "Выберите новый уровень прав:"
    ),
    ListGroup(
        Button(
            Format("🔸 {item[name]} - {item[description]}"),
            id="edit_pre",
            on_click=on_permission_level_selected,  # type: ignore
        ),
        id="permission_level",
        item_id_getter=lambda item: str(item["level"]),
        items="permission_levels",
    ),
    Button(Const("🚫 Удалить мастера"), id="remove_user", on_click=on_remove_user),
    SwitchTo(
        Const("⬅️ Назад к списку"), id="back", state=campaign_states.EditPermissions.main
    ),
    state=campaign_states.EditPermissions.select_permission,
    getter=get_user_permission_data,
)

# Окно добавление мастера
invite_master_window = Window(
    Const("Напишите @username нового мастера"),
    SwitchTo(
        Const("⬅️ Назад к списку"), id="back", state=campaign_states.EditPermissions.main
    ),
    TextInput(id="master_username", on_success=on_invite_user),
    state=campaign_states.EditPermissions.invite_master,
)

# === СОЗДАНИЕ ДИАЛОГА И РОУТЕРА ===

permissions_dialog = Dialog(
    permissions_main_window,
    select_permission_window,
    invite_master_window,
)

router = Router()
router.include_router(permissions_dialog)
