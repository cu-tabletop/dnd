from ninja import Schema
from typing import Optional, List


class PlayerSearchSchema(Schema):
    telegram_id: Optional[int] = None
    username: Optional[str] = None


class PlayerResponse(Schema):
    id: int
    telegram_id: int
    telegram_username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]


class PlayerUpdateRequest(Schema):
    telegram_id: int
    telegram_username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
