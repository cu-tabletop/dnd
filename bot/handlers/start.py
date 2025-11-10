from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager

from states.mainmenu import MainMenu

router = Router()


@router.message(CommandStart())
async def start_command(
    message: Message, dialog_manager: DialogManager
) -> None:
    await dialog_manager.start(MainMenu.main)
