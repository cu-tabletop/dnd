from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from . import states

if TYPE_CHECKING:
    from db.models.user import User

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, dialog_manager: DialogManager):
    user: User = dialog_manager.middleware_data["user"]

    welcome_text = (
        f"Приветствую вас, Мастер {user.username}!\n\n"
        "Я ваш верный помощник в организации настольных ролевых игр.\n"
        "Давайте начнем наше приключение!"
    )

    await message.answer(welcome_text)

    await dialog_manager.start(
        state=states.CampaignList.main,
        mode=StartMode.RESET_STACK,
        data={"user_id": user.id},
    )
