import enum

from aiogram.fsm.state import State, StatesGroup


class InventoryView(StatesGroup):
    view = State()
    preview = State()


class TargetType(enum.IntEnum):
    USER = 0
    CHARACTER = 1
