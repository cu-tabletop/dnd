import logging
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from states import states
from services.api_client import api_client

router = Router()

logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, dialog_manager: DialogManager):
    user = message.from_user

    welcome_text = (
        f"Приветствую вас, Игрок {user.first_name}!\n\n"
        "Я ваш верный помощник в организации настольных ролевых игр.\n"
        "Давайте начнем наше приключение!"
    )

    await message.answer(welcome_text)

    await api_client.update_player_info(
        user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    await dialog_manager.start(
        state=states.Menu.main,
        mode=StartMode.RESET_STACK,
        data={"user_id": user.id},
    )
