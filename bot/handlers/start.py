import logging
from aiogram import Bot, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from states import states

router = Router()

logger = logging.getLogger(__name__)


# @router.message(CommandStart())
# async def start_command(
#     message: Message, dialog_manager: DialogManager
# ) -> None:
#     await dialog_manager.start(MainMenu.main)


@router.message(CommandStart())
async def cmd_start(message: Message, dialog_manager: DialogManager):
    user = message.from_user

    welcome_text = (
        f"Приветствую вас, Мастер {user.first_name}!\n\n"
        "Я ваш верный помощник в организации настольных ролевых игр.\n"
        "Давайте начнем наше приключение!"
    )

    await message.answer(welcome_text)

    await dialog_manager.start(
        state=states.MainMenu.main,
        mode=StartMode.RESET_STACK,
        data={"user_id": user.id},
    )


@router.message(CommandStart())
async def start_command(message: Message, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(MainMenu.main)
