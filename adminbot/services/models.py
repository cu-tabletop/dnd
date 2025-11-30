from pydantic import BaseModel
from typing import Optional

# from enum import IntEnum
from datetime import datetime


# Базовые схемы
class Message(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str


# Player schemas
class PlayerResponse(BaseModel):
    id: int
    telegram_id: int
    telegram_username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]


# Invitation schemas
class InvitationResponse(BaseModel):
    id: int
    campaign_id: int
    campaign_title: str
    invited_player_telegram_id: int
    invited_by_telegram_id: int
    status: str
    token: str
    expires_at: datetime
    created_at: datetime


# Campaign schemas
class CampaignModelSchema(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = ""
    icon: Optional[str] = None
    verified: bool = False
    private: bool = False


class CreateCampaignResponse(Message):
    pass


# Character schemas
class CharacterOut(BaseModel):
    id: int
    owner_id: int
    owner_telegram_id: int
    campaign_id: int
    data: dict


class GetCharacterResponse(CharacterOut):
    pass


class UploadCharacterResponse(CharacterOut):
    pass


# Inventory schemas
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


class AddInventoryItemResponse(InventoryItem):
    pass


class UpdateInventoryItemResponse(InventoryItem):
    pass


class DeleteInventoryItemResponse(Message):
    pass


# Response types
class PingResponse(Message):
    pass
