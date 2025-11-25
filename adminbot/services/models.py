from pydantic import BaseModel
from typing import Any, Union
from enum import IntEnum


class Message(BaseModel):
    message: str


class ValidationError(BaseModel):
    message: Union[str, dict[str, Any], list[Any]] = "Ошибка в данных запроса."


class NotFoundError(BaseModel):
    message: str = "Объект не найден"


class ForbiddenError(BaseModel):
    message: str = "Запрещено"


class CharacterOut(BaseModel):
    id: int
    owner_id: int
    owner_telegram_id: int
    campaign_id: int
    data: dict[str, Any]


class UploadCharacter(BaseModel):
    owner_id: int
    campaign_id: int
    data: dict[str, Any]


class CreateCampaignRequest(BaseModel):
    telegram_id: int
    title: str
    icon: str | None = None
    description: str | None = None


class CampaignModelSchema(BaseModel):
    id: int | None = None
    title: str
    description: str | None = ""
    icon: str | None = None
    verified: bool = False
    private: bool = False


class AddToCampaignRequest(BaseModel):
    campaign_id: int
    owner_id: int
    user_id: int


class CampaignPermissions(IntEnum):
    PARTICIPANT = 0
    EDITOR = 1
    OWNER = 2


class CampaignEditPermissions(BaseModel):
    campaign_id: int
    owner_id: int
    user_id: int
    status: CampaignPermissions


# Response types for API methods
class PingResponse(Message):
    pass


class GetCharacterResponse(CharacterOut):
    pass


class UploadCharacterResponse(CharacterOut):
    pass


class CreateCampaignResponse(Message):
    pass


class GetCampaignsResponse(BaseModel):
    __root__: Union[CampaignModelSchema, list[CampaignModelSchema]]


class AddToCampaignResponse(Message):
    pass


class EditPermissionsResponse(Message):
    pass


# Error response type
class ErrorResponse(BaseModel):
    error: Union[ValidationError, NotFoundError, ForbiddenError, str]
