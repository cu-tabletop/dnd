from aiogram.fsm.state import StatesGroup, State


class CampaignCreate(StatesGroup):
    name = State()
    description = State()
    icon = State()
    privacy = State()
    confirm = State()
