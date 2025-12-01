from aiogram.fsm.state import StatesGroup, State


class UploadCharacter(StatesGroup):
    upload = State()
