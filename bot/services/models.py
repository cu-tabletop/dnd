from pydantic import BaseModel
from typing import Optional, Union, List
from enum import IntEnum
from pydantic import RootModel


class Message(BaseModel):
    message: str


class ValidationError(BaseModel):
    message: Union[str, dict, list] = "Ошибка в данных запроса."


class NotFoundError(BaseModel):
    message: str = "Объект не найден"


class ForbiddenError(BaseModel):
    message: str = "Запрещено"


class CharacterOut(BaseModel):
    id: int
    owner_id: int
    owner_telegram_id: int
    campaign_id: int
    data: dict


class UploadCharacter(BaseModel):
    owner_id: int
    campaign_id: int
    data: dict


class CreateCampaignRequest(BaseModel):
    telegram_id: int
    title: str
    icon: Optional[str] = None  # tgmedia_id
    description: Optional[str] = None


class UpdateCampaignRequest(BaseModel):
    telegram_id: int
    campaign_id: int
    title: Optional[str]
    icon: Optional[str] = None  # tgmedia_id
    description: Optional[str] = None


class CampaignModelSchema(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = ""
    icon: Optional[str] = None  # tgmedia_id
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


class GetCampaignsResponse(RootModel):
    root: Union[CampaignModelSchema, List[CampaignModelSchema]]


class AddToCampaignResponse(Message):
    pass


class EditPermissionsResponse(Message):
    pass


# Error response type
class ErrorResponse(BaseModel):
    error: Union[ValidationError, NotFoundError, ForbiddenError, str]


class InventoryItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    quantity: int = 1


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = None


class InventoryItem(InventoryItemBase):
    id: int
    character_id: int


# Response types for inventory
class GetInventoryResponse(RootModel):
    root: List[InventoryItem]


class AddInventoryItemResponse(InventoryItem):
    pass


class UpdateInventoryItemResponse(InventoryItem):
    pass


class DeleteInventoryItemResponse(Message):
    pass
