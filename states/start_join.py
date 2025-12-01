from aiogram.fsm.state import StatesGroup, State


class StartJoin(StatesGroup):
    invitation = State()
