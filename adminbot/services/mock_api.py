import logging
import asyncio
import random
from datetime import datetime
from typing import Optional, List, Union


from settings import settings
from .models import (
    AddInventoryItemResponse,
    DeleteInventoryItemResponse,
    InventoryItem,
    InventoryItemCreate,
    InventoryItemUpdate,
    PingResponse,
    GetCharacterResponse,
    UpdateInventoryItemResponse,
    UploadCharacterResponse,
    CreateCampaignResponse,
    AddToCampaignResponse,
    EditPermissionsResponse,
    ErrorResponse,
    CharacterOut,
    CampaignModelSchema,
    CampaignPermissions,
)

logger = logging.getLogger(__name__)


class MockDnDApiClient:
    """Заглушка API для тестирования с полной реализацией всех эндпоинтов"""

    def __init__(self):
        # Создаем простые base64 иконки для моков
        self.default_icon_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="  # 1x1 прозрачный пиксель

        self.campaigns = [
            CampaignModelSchema(
                id=1,
                title="🦁 Грифондор",
                description="Факультет храбрости и благородства",
                icon=self.default_icon_base64,
                verified=True,
                private=False,
            ),
            CampaignModelSchema(
                id=2,
                title="🐍 Слизерин",
                description="Факультет амбициозных и хитрых",
                icon=self.default_icon_base64,
                verified=True,
                private=False,
            ),
        ]
        self.characters = [
            CharacterOut(
                id=1,
                owner_id=123,
                owner_telegram_id=123,
                campaign_id=1,
                data={
                    "name": "Элриндор",
                    "level": 5,
                    "rating": -1,
                    "class": "🧙‍♂️ Маг",
                    "race": "Эльф",
                    "player": "Алексей",
                    "hp_current": 32,
                    "hp_max": 32,
                    "xp": 2500,
                    "status": "активен",
                    "last_activity": "2024-01-15",
                },
            ),
            CharacterOut(
                id=2,
                owner_id=124,
                owner_telegram_id=124,
                campaign_id=1,
                data={
                    "name": "Торгрим",
                    "level": 4,
                    "rating": 10,
                    "class": "⚔️ Воин",
                    "race": "Дварф",
                    "player": "Дмитрий",
                    "hp_current": 45,
                    "hp_max": 45,
                    "xp": 1800,
                    "status": "активен",
                    "last_activity": "2024-01-14",
                },
            ),
        ]
        self.inventory_items = [
            InventoryItem(
                id=1,
                character_id=1,
                name="Меч света",
                description="Магический меч, светящийся в темноте",
                quantity=1,
            ),
            InventoryItem(
                id=2,
                character_id=1,
                name="Зелье здоровья",
                description="Восстанавливает 50 HP",
                quantity=3,
            ),
            InventoryItem(
                id=3,
                character_id=2,
                name="Топор варвара",
                description="Массивный двуручный топор",
                quantity=1,
            ),
        ]
        self.next_inventory_id = 4
        self.next_campaign_id = 3
        self.next_character_id = 3
        self.campaign_permissions = {}

    async def _simulate_delay(self):
        """Имитация задержки сети"""
        await asyncio.sleep(random.uniform(0.1, settings.STUB_DELAY))

    # === PING ===
    async def ping(self) -> PingResponse:
        await self._simulate_delay()
        return PingResponse(message="pong")

    # === CHARACTER ENDPOINTS ===
    async def get_character(
        self, char_id: int
    ) -> Optional[GetCharacterResponse]:
        await self._simulate_delay()
        for character in self.characters:
            if character.id == char_id:
                return GetCharacterResponse.model_validate(
                    character.model_dump()
                )
        return None

    async def upload_character(
        self, owner_id: int, campaign_id: int, data: dict
    ) -> Union[UploadCharacterResponse, ErrorResponse]:
        await self._simulate_delay()

        campaign_exists = any(
            campaign.id == campaign_id for campaign in self.campaigns
        )
        if not campaign_exists:
            return ErrorResponse(error="Кампания не найдена")

        new_character = CharacterOut(
            id=self.next_character_id,
            owner_id=owner_id,
            owner_telegram_id=owner_id,
            campaign_id=campaign_id,
            data=data,
        )

        self.characters.append(new_character)
        self.next_character_id += 1

        return UploadCharacterResponse.model_validate(
            new_character.model_dump()
        )

    async def get_campaign_characters(
        self, campaign_id: int
    ) -> List[GetCharacterResponse]:
        await self._simulate_delay()
        return [
            GetCharacterResponse.model_validate(char.model_dump())
            for char in self.characters
            if char.campaign_id == campaign_id
        ]

    async def update_character(
        self, char_id: int, update_data: dict
    ) -> Union[GetCharacterResponse, ErrorResponse]:
        await self._simulate_delay()

        for character in self.characters:
            if character.id == char_id:
                character.data.update(update_data)
                character.data["last_activity"] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                )
                return GetCharacterResponse.model_validate(
                    character.model_dump()
                )

        return ErrorResponse(error="Персонаж не найден")

    # === INVENTORY ENDPOINTS ===
    async def get_character_inventory(
        self, character_id: int
    ) -> List[InventoryItem]:
        """Получить инвентарь персонажа"""
        await self._simulate_delay()
        return [
            item
            for item in self.inventory_items
            if item.character_id == character_id
        ]

    async def add_inventory_item(
        self, character_id: int, item: InventoryItemCreate
    ) -> Union[AddInventoryItemResponse, ErrorResponse]:
        """Добавить предмет в инвентарь"""
        await self._simulate_delay()

        # Проверяем существование персонажа
        character_exists = any(
            char.id == character_id for char in self.characters
        )
        if not character_exists:
            return ErrorResponse(error="Персонаж не найден")

        new_item = InventoryItem(
            id=self.next_inventory_id,
            character_id=character_id,
            name=item.name,
            description=item.description,
            quantity=item.quantity,
        )

        self.inventory_items.append(new_item)
        self.next_inventory_id += 1

        return AddInventoryItemResponse(**new_item.model_dump())

    async def update_inventory_item(
        self, item_id: int, update_data: InventoryItemUpdate
    ) -> Union[UpdateInventoryItemResponse, ErrorResponse]:
        """Обновить предмет в инвентаре"""
        await self._simulate_delay()

        for item in self.inventory_items:
            if item.id == item_id:
                # Обновляем поля
                if update_data.name is not None:
                    item.name = update_data.name
                if update_data.description is not None:
                    item.description = update_data.description
                if update_data.quantity is not None:
                    item.quantity = update_data.quantity

                return UpdateInventoryItemResponse(**item.model_dump())

        return ErrorResponse(error="Предмет не найден")

    async def delete_inventory_item(
        self, item_id: int
    ) -> Union[DeleteInventoryItemResponse, ErrorResponse]:
        """Удалить предмет из инвентаря"""
        await self._simulate_delay()

        for i, item in enumerate(self.inventory_items):
            if item.id == item_id:
                self.inventory_items.pop(i)
                return DeleteInventoryItemResponse(message="Предмет удален")

        return ErrorResponse(error="Предмет не найден")

    # === CAMPAIGN ENDPOINTS ===
    async def get_campaigns(
        self, user_id: Optional[int] = None, campaign_id: Optional[int] = None
    ) -> List[CampaignModelSchema]:
        await self._simulate_delay()

        if campaign_id:
            return [camp for camp in self.campaigns if camp.id == campaign_id]

        return self.campaigns

    async def create_campaign(
        self,
        telegram_id: int,
        title: str,
        description: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> Union[CreateCampaignResponse, ErrorResponse]:
        await self._simulate_delay()

        new_campaign = CampaignModelSchema(
            id=telegram_id,
            title=title,
            description=description or "Описание отсутствует",
            icon=icon or self.default_icon_base64,
            verified=False,
            private=False,
        )

        self.campaigns.append(new_campaign)
        self.next_campaign_id += 1

        return CreateCampaignResponse(
            message=f"Кампания '{title}' создана успешно"
        )

    async def add_to_campaign(
        self, campaign_id: int, owner_id: int, user_id: int
    ) -> Union[AddToCampaignResponse, ErrorResponse]:
        await self._simulate_delay()

        campaign_exists = any(
            campaign.id == campaign_id for campaign in self.campaigns
        )
        if not campaign_exists:
            return ErrorResponse(error="Кампания не найдена")

        return AddToCampaignResponse(
            message=f"Пользователь {user_id} добавлен в кампанию {campaign_id}"
        )

    async def edit_permissions(
        self,
        campaign_id: int,
        owner_id: int,
        user_id: int,
        status: CampaignPermissions,
    ) -> Union[EditPermissionsResponse, ErrorResponse]:
        await self._simulate_delay()

        campaign_exists = any(
            campaign.id == campaign_id for campaign in self.campaigns
        )
        if not campaign_exists:
            return ErrorResponse(error="Кампания не найдена")

        if campaign_id not in self.campaign_permissions:
            self.campaign_permissions[campaign_id] = {}
        self.campaign_permissions[campaign_id][user_id] = status

        status_names = {0: "Участник", 1: "Мастер", 2: "Владелец"}
        return EditPermissionsResponse(
            message=f"Права пользователя {user_id} изменены на: {status_names.get(status.value, 'Неизвестно')}"
        )
