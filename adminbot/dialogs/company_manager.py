import logging
from aiogram import Router
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import (
    Row,
    Start,
    Cancel,
    Select,
    ScrollingGroup,
)
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput
from aiogram.types import Message, CallbackQuery, User

# from aiogram_dialog.api.entities import ShowMode

from services.api_client import get_api_client
from models.models import CompanyCreate
from .states import (
    CompanyManagerSG1,
    CompanyManagerSG2,
    CompanyManagerSG3,
    CompanyWorkSG,
)

api_client = get_api_client()
logger = logging.getLogger(__name__)

# ========== ГЕТТЕРЫ ==========


async def get_user_companies(
    dialog_manager: DialogManager, event_from_user: User, **kwargs
):
    """Получение компаний пользователя"""
    user_id = event_from_user.id
    companies = await api_client.get_user_companies(user_id)
    return {
        "companies": companies,
        "has_companies": len(companies) > 0,
        "user_id": user_id,
    }


async def get_selected_company(dialog_manager: DialogManager, **kwargs):
    """Получение выбранной компании"""

    return {
        "company_name": dialog_manager.dialog_data.get("company_name", "Неизвестно")
    }
    # lambda dialog_manager, **kwargs: {
    #     "company_name": dialog_manager.dialog_data.get("company_name", "Неизвестно")
    # },


# ========== ОБРАБОТЧИКИ ==========


async def on_company_selected(
    callback: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    """Обработчик выбора компании"""
    company_id = int(item_id)
    manager.dialog_data["company_id"] = company_id

    # Сохраняем информацию о компании
    companies = await api_client.get_user_companies(callback.from_user.id)
    selected_company = next((c for c in companies if c.id == company_id), None)
    if selected_company:
        manager.dialog_data["company_name"] = selected_company.name

    await manager.start(CompanyWorkSG.main)
    # await manager.switch_to(CompanyManagerSG.company_selected)


async def on_company_name_input(
    message: Message, widget: ManagedTextInput, manager: DialogManager, **kwargs
):
    """Обработчик ввода названия компании"""
    logger.info("дошло")
    text = kwargs["text"]

    if not text.strip():
        await message.answer("❌ Название компании не может быть пустым")
        return

    user_id = message.from_user.id  # type: ignore
    company_data = CompanyCreate(name=text.strip())

    try:
        new_company = await api_client.create_company(user_id, company_data)
        await message.answer(f"✅ Компания '{new_company.name}' создана!")
        await manager.done()
    except Exception as e:
        logger.error(f"Error creating company: {e}")
        await message.answer("❌ Ошибка при создании компании")


async def on_company_deletion_confirm(
    callback: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    """Обработчик подтверждения удаления компании"""
    company_id = int(item_id)

    try:
        await api_client.delete_company(company_id)
        await callback.answer("✅ Компания удалена")
        await manager.done()
    except Exception as e:
        logger.error(f"Error deleting company: {e}")
        await callback.answer("❌ Ошибка при удалении компании")


# async def on_work_with_company(
#     callback: CallbackQuery, button: Button, manager: DialogManager
# ):
#     """Обработчик работы с компанией"""
#     await manager.start(CompanyWorkSG.main)


# ========== ОКНА ДИАЛОГА ==========

# Главное окно менеджера компаний
main_dialog = Dialog(
    Window(
        Multi(
            Const("🏢 Управление компаниями"),
            Const(""),
            Format("Ваши компании:"),
            sep="\n",
        ),
        Const(
            "📝 У вас пока нет компаний. Создайте первую!",
            when=lambda data, *args, **kwargs: not data["has_companies"],
        ),
        ScrollingGroup(
            Select(
                Format("{item.name}"),
                id="s_companies",
                item_id_getter=lambda item: item.id,
                items="companies",
                on_click=on_company_selected,
            ),
            id="companies_scroll",
            width=1,
            height=6,
            when="has_companies",
        ),
        Row(
            Start(
                Const("➕ Создать компанию"),
                id="add_company",
                state=CompanyManagerSG2.add_company,
            ),
            Start(
                Const("🗑️ Удалить компанию"),
                id="delete_company",
                state=CompanyManagerSG3.delete_company,
            ),
        ),
        # Cancel(Const("❌ Выход")),
        state=CompanyManagerSG1.main,
        getter=get_user_companies,
    )
)

# Окно создания компании
add_company_dialog = Dialog(
    Window(
        Const("🏗️ Создание новой компании\n\nВведите название компании:"),
        TextInput(
            id="company_name_input",
            on_success=on_company_name_input,
        ),
        Cancel(Const("⬅️ Назад")),
        state=CompanyManagerSG2.add_company,
    )
)

# Окно удаления компании
delete_company_dialog = Dialog(
    Window(
        Const("🗑️ Удаление компании\n\nВыберите компанию для удаления:"),
        ScrollingGroup(
            Select(
                Format("{item.name}"),
                id="s_companies_delete",
                item_id_getter=lambda item: item.id,
                items="companies",
                on_click=on_company_deletion_confirm,
            ),
            id="companies_delete_scroll",
            width=1,
            height=6,
        ),
        Cancel(Const("⬅️ Назад")),
        state=CompanyManagerSG3.delete_company,
        getter=get_user_companies,
    )
)

# Окно выбранной компании
# company_selected_window = Window(
#     Format("🏢 Компания: {company_name}"),
#     Const("\nВыберите действие:"),
#     Group(
#         Button(
#             Const("🚀 Работа с компанией"),
#             id="work_with_company",
#             on_click=on_work_with_company,
#         ),
#         # Button(Const("📊 Статистика компании"), id="company_stats"),
#     ),
#     Back(Const("⬅️ К списку компаний")),
#     state=CompanyManagerSG.company_selected,
#     getter=get_selected_company,
# )


router = Router()
router.include_routers(main_dialog, add_company_dialog, delete_company_dialog)
