from aiogram.fsm.state import StatesGroup, State


class AcademyRating(StatesGroup):
    rating = State()
