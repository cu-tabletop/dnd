from aiogram.fsm.state import State, StatesGroup


class OtherGames(StatesGroup):
    main = State()
    available = State()
