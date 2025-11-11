import logging
from aiogram import Router
from aiogram.types.users_shared import UsersShared
from aiogram.types.keyboard_button import KeyboardButton
from aiogram.types.reply_keyboard_markup import ReplyKeyboardMarkup
from aiogram.types.keyboard_button_request_users import KeyboardButtonRequestUsers
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Group, Back, Cancel, Start
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput
from aiogram.types import Message, CallbackQuery

# from aiogram_dialog.api.entities import ShowMode

from services.api_client import get_api_client
from .states import CompanyWorkSG, CharacterManagerSG

api_client = get_api_client()
logger = logging.getLogger(__name__)

# ========== ГЕТТЕРЫ ==========


async def get_company_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных о компании"""
    company_id = dialog_manager.dialog_data.get("company_id")
    company_name = dialog_manager.dialog_data.get("company_name", "Неизвестно")
    return {"company_id": company_id, "company_name": company_name}


# ========== ОБРАБОТЧИКИ ==========


async def on_character_manager(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    """Обработчик перехода к менеджеру персонажей"""
    await manager.start(CharacterManagerSG.main)


async def on_master_username_input(
    message: Message, widget: ManagedTextInput, manager: DialogManager, text: str
):
    """Обработчик ввода username мастера"""
    username = text.strip()
    if not username:
        await message.answer("❌ Username не может быть пустым")
        return

    # Убедимся что username начинается с @
    if not username.startswith("@"):
        username = f"@{username}"

    company_id = manager.dialog_data.get("company_id")

    try:
        await api_client.add_master_to_company(company_id, username)  # type: ignore
        await message.answer(f"✅ Мастер {username} добавлен к компании!")
        await manager.switch_to(CompanyWorkSG.main)
    except Exception as e:
        logger.error(f"Error adding master: {e}")
        await message.answer("❌ Ошибка при добавлении мастера")


request_user_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="Выбрать пользователя",
                request_users=KeyboardButtonRequestUsers(
                    request_id=1, user_is_bot=False  # Только пользователи, не боты
                ),
            )
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


async def add_master(
    message: Message, widget: ManagedTextInput, manager: DialogManager
):
    """Обработчик ввода username мастера"""

    await message.answer("👥 Выберите новых мастеров", reply_markup=request_user_kb)


# ========== ОКНА ДИАЛОГА ==========

# Главное окно работы с компанией
main_dialog = Dialog(
    Window(
        Multi(
            Format("🚀 Работа с компанией: {company_name}"),
            Const(""),
            Const("Доступные действия:"),
            sep="\n",
        ),
        Group(
            Button(
                Const("👥 Добавить мастера"),
                id="add_master",
                on_click=add_master,
            ),
            Start(
                Const("🧙 Менеджер персонажей"),
                id="character_manager",
                state=CharacterManagerSG.main,
            ),
            Button(Const("📊 Статистика"), id="stats"),
            Button(Const("⚙️ Настройки"), id="settings"),
        ),
        Cancel(Const("⬅️ К компаниям")),
        state=CompanyWorkSG.main,
        getter=get_company_data,
    )
)

# Окно добавления мастера
add_master_dialog = Dialog(
    Window(
        Multi(
            Format("👥 Добавлены мастера"),
            Format("Компания: {company_name}"),
            Const(""),
            Const("Введите @username мастера:"),
            sep="\n",
        ),
        # Button(Const("выбрать"), id="select_users", on_click=select_users),
        # TextInput(
        #     id="master_username_input",
        #     on_success=on_master_username_input,
        # ),
        Cancel(Const("⬅️ Назад")),
        state=CompanyWorkSG.add_master,
        getter=get_company_data,
    )
)

router = Router()

router.message(UsersShared)(on_character_manager)

router.include_routers(main_dialog, add_master_dialog)
