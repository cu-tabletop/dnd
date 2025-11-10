from aiogram.fsm.state import StatesGroup, State


class MainMenu(StatesGroup):
    main = State()
    campaigns = State()
    oneshots = State()
    academy = State()
