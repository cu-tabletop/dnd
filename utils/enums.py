import enum


class Role(enum.IntEnum):
    PLAYER = 0
    MASTER = 1
    OWNER = 2


class Mode(enum.StrEnum):
    """Режим работы основного меня admin бота"""

    Base = "Базовый"
    Academy = "Академия"
