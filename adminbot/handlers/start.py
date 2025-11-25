from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode
from services.api_client import get_api_client, USE_MOCK_API
from dialogs import states as campaign_states

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, dialog_manager: DialogManager):
    user = message.from_user
    mode = "мок-данные" if USE_MOCK_API else "реальное API"

    welcome_text = (
        f"Приветствую вас, Мастер {user.first_name}!\n\n"
        "Я ваш верный помощник в организации настольных ролевых игр.\n"
        f"📊 Режим работы: {mode}\n\n"
        "Давайте начнем наше приключение!"
    )

    await message.answer(welcome_text)

    await dialog_manager.start(
        state=campaign_states.CampaignManagerMain.main,
        mode=StartMode.RESET_STACK,
        data={"user_id": user.id},
    )


@router.message(Command("mock"))
async def cmd_mock(message: Message):
    """Включить режим моков"""
    global USE_MOCK_API, api_client
    USE_MOCK_API = True
    api_client = get_api_client()
    await message.answer("✅ Режим мок-API активирован. Используются тестовые данные.")


@router.message(Command("real"))
async def cmd_real(message: Message):
    """Включить режим реального API"""
    global USE_MOCK_API, api_client
    USE_MOCK_API = False
    api_client = get_api_client()

    # Проверяем соединение с реальным API
    try:
        result = await api_client.ping()
        await message.answer(
            f"✅ Режим реального API активирован. Ping: {result.message}"
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось подключиться к API: {str(e)}")


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Показать текущий режим API"""
    mode = "мок-данные" if USE_MOCK_API else "реальное API"

    # Тестируем соединение
    try:
        ping_result = await api_client.ping()
        status = f"✅ Соединение: {ping_result.message}"
    except Exception as e:
        status = f"❌ Ошибка соединения: {str(e)}"

    await message.answer(
        f"📊 Текущий режим: {mode}\n"
        f"{status}\n\n"
        f"Используйте команды:\n"
        f"/mock - переключиться на тестовые данные\n"
        f"/real - переключиться на реальное API"
    )
