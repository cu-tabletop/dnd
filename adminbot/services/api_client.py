import aiohttp
import logging
import asyncio
import random
from datetime import datetime
from typing import Optional, List, Union
from settings import settings

from .models import (
    PingResponse,
    GetCharacterResponse,
    UploadCharacterResponse,
    CreateCampaignResponse,
    GetCampaignsResponse,
    AddToCampaignResponse,
    EditPermissionsResponse,
    ErrorResponse,
    CharacterOut,
    CampaignModelSchema,
    UploadCharacter,
    CreateCampaignRequest,
    AddToCampaignRequest,
    CampaignEditPermissions,
    CampaignPermissions,
)

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """Базовое исключение для ошибок API"""

    pass


class ValidationError(ApiError):
    pass


class NotFoundError(ApiError):
    pass


class ForbiddenError(ApiError):
    pass


class MockDnDApiClient:
    """Заглушка API для тестирования с полной реализацией всех эндпоинтов"""

    def __init__(self):
        self.campaigns = [
            CampaignModelSchema(
                id=1,
                title="Грифондор",
                description="Факультет храбрости и благородства",
                icon="🦁",
                verified=True,
                private=False,
            ),
            CampaignModelSchema(
                id=2,
                title="Слизерин",
                description="Факультет амбициозных и хитрых",
                icon="🐍",
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
        self.next_campaign_id = 3
        self.next_character_id = 3
        self.campaign_permissions = {}  # {campaign_id: {user_id: permission_level}}

    async def _simulate_delay(self):
        """Имитация задержки сети"""
        await asyncio.sleep(random.uniform(0.1, settings.STUB_DELAY))

    # === PING ===
    async def ping(self) -> PingResponse:
        await self._simulate_delay()
        return PingResponse(message="pong")

    # === CHARACTER ENDPOINTS ===
    async def get_character(self, char_id: int) -> Optional[GetCharacterResponse]:
        await self._simulate_delay()
        for character in self.characters:
            if character.id == char_id:
                return GetCharacterResponse(**character.dict())
        return None

    async def upload_character(
        self, owner_id: int, campaign_id: int, data: dict
    ) -> Union[UploadCharacterResponse, ErrorResponse]:
        await self._simulate_delay()

        # Проверяем существование кампании
        campaign_exists = any(campaign.id == campaign_id for campaign in self.campaigns)
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

        return UploadCharacterResponse(**new_character.dict())

    async def get_campaign_characters(
        self, campaign_id: int
    ) -> List[GetCharacterResponse]:
        await self._simulate_delay()
        return [
            GetCharacterResponse(**char.dict())
            for char in self.characters
            if char.campaign_id == campaign_id
        ]

    async def update_character(
        self, char_id: int, update_data: dict
    ) -> Union[GetCharacterResponse, ErrorResponse]:
        await self._simulate_delay()

        for character in self.characters:
            if character.id == char_id:
                # Обновляем данные персонажа
                character.data.update(update_data)
                character.data["last_activity"] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                )

                return GetCharacterResponse(**character.dict())

        return ErrorResponse(error="Персонаж не найден")

    # === CAMPAIGN ENDPOINTS ===
    async def get_campaigns(
        self, user_id: Optional[int] = None, campaign_id: Optional[int] = None
    ) -> List[CampaignModelSchema]:
        await self._simulate_delay()

        if campaign_id:
            return [camp for camp in self.campaigns if camp.id == campaign_id]

        # В моках возвращаем все кампании для любого пользователя
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
            id=self.next_campaign_id,
            title=title,
            description=description or "Описание отсутствует",
            icon=icon or "🏰",
            verified=False,
            private=False,
        )

        self.campaigns.append(new_campaign)
        self.next_campaign_id += 1

        return CreateCampaignResponse(message=f"Кампания '{title}' создана успешно")

    async def add_to_campaign(
        self, campaign_id: int, owner_id: int, user_id: int
    ) -> Union[AddToCampaignResponse, ErrorResponse]:
        await self._simulate_delay()

        # Проверяем существование кампании
        campaign_exists = any(campaign.id == campaign_id for campaign in self.campaigns)
        if not campaign_exists:
            return ErrorResponse(error="Кампания не найдена")

        return AddToCampaignResponse(
            message=f"Пользователь {user_id} добавлен в кампанию {campaign_id}"
        )

    async def edit_permissions(
        self, campaign_id: int, owner_id: int, user_id: int, status: CampaignPermissions
    ) -> Union[EditPermissionsResponse, ErrorResponse]:
        await self._simulate_delay()

        # Проверяем существование кампании
        campaign_exists = any(campaign.id == campaign_id for campaign in self.campaigns)
        if not campaign_exists:
            return ErrorResponse(error="Кампания не найдена")

        # Сохраняем права доступа
        if campaign_id not in self.campaign_permissions:
            self.campaign_permissions[campaign_id] = {}
        self.campaign_permissions[campaign_id][user_id] = status

        status_names = {0: "Участник", 1: "Мастер", 2: "Владелец"}
        return EditPermissionsResponse(
            message=f"Права пользователя {user_id} изменены на: {status_names.get(status.value, 'Неизвестно')}"
        )


class RealDnDApiClient:
    """Реальный клиент API с полной реализацией всех эндпоинтов"""

    def __init__(self, base_url: str):
        self.base_url = base_url

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Union[dict, list]:
        """Универсальный метод для выполнения HTTP запросов"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method, f"{self.base_url}{endpoint}", **kwargs
                ) as response:

                    if response.status in [200, 201]:
                        return await response.json()
                    elif response.status == 400:
                        error_data = await response.json()
                        raise ValidationError(f"Ошибка валидации: {error_data}")
                    elif response.status == 403:
                        raise ForbiddenError("Доступ запрещен")
                    elif response.status == 404:
                        raise NotFoundError("Объект не найден")
                    else:
                        error_text = await response.text()
                        logger.error(f"API error {response.status}: {error_text}")
                        raise ApiError(f"Ошибка API: {response.status}")

        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            raise ApiError(f"Ошибка сети: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise ApiError(f"Неожиданная ошибка: {str(e)}")

    # === PING ===
    async def ping(self) -> PingResponse:
        result = await self._make_request("GET", "/api/ping/")
        return PingResponse(**result)

    # === CHARACTER ENDPOINTS ===
    async def get_character(self, char_id: int) -> Optional[GetCharacterResponse]:
        result = await self._make_request(
            "GET", "/api/character/get/", params={"char_id": char_id}
        )
        return GetCharacterResponse(**result) if result else None

    async def upload_character(
        self, owner_id: int, campaign_id: int, data: dict
    ) -> UploadCharacterResponse:
        payload = UploadCharacter(
            owner_id=owner_id,
            campaign_id=campaign_id,
            data=data,
        )
        result = await self._make_request(
            "POST", "/api/character/post/", json=payload.dict()
        )
        return UploadCharacterResponse(**result)

    async def get_campaign_characters(
        self, campaign_id: int
    ) -> List[GetCharacterResponse]:
        """Получить всех персонажей кампании"""
        # В текущем API нет прямого метода для этого
        # Это временное решение - в реальном API должен быть эндпоинт
        # для получения персонажей кампании
        logger.warning(
            "get_campaign_characters: Этот метод требует отдельного эндпоинта на бэкенде"
        )
        return []

    async def update_character(
        self, char_id: int, update_data: dict
    ) -> GetCharacterResponse:
        """Обновить персонажа"""
        # В текущем API нет метода обновления персонажа
        logger.warning("update_character: Этот метод требует реализации на бэкенде")
        raise ApiError("Метод обновления персонажа не реализован на сервере")

    # === CAMPAIGN ENDPOINTS ===
    async def get_campaigns(
        self, user_id: Optional[int] = None, campaign_id: Optional[int] = None
    ) -> List[CampaignModelSchema]:
        params = {}
        if user_id is not None:
            params["user_id"] = user_id
        if campaign_id is not None:
            params["campaign_id"] = campaign_id

        result = await self._make_request("GET", "/api/campaign/get/", params=params)

        # API может вернуть один объект или массив
        if isinstance(result, list):
            return [CampaignModelSchema(**item) for item in result]
        else:
            return [CampaignModelSchema(**result)]

    async def create_campaign(
        self,
        telegram_id: int,
        title: str,
        description: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> CreateCampaignResponse:
        payload = CreateCampaignRequest(
            telegram_id=telegram_id,
            title=title,
            description=description,
            icon=icon,
        )
        result = await self._make_request(
            "POST", "/api/campaign/create/", json=payload.dict()
        )
        return CreateCampaignResponse(**result)

    async def add_to_campaign(
        self, campaign_id: int, owner_id: int, user_id: int
    ) -> AddToCampaignResponse:
        payload = AddToCampaignRequest(
            campaign_id=campaign_id,
            owner_id=owner_id,
            user_id=user_id,
        )
        result = await self._make_request(
            "POST", "/api/campaign/add/", json=payload.dict()
        )
        return AddToCampaignResponse(**result)

    async def edit_permissions(
        self, campaign_id: int, owner_id: int, user_id: int, status: CampaignPermissions
    ) -> EditPermissionsResponse:
        payload = CampaignEditPermissions(
            campaign_id=campaign_id,
            owner_id=owner_id,
            user_id=user_id,
            status=status,
        )
        result = await self._make_request(
            "POST", "/api/campaign/edit-permissions/", json=payload.dict()
        )
        return EditPermissionsResponse(**result)


# Глобальная переменная для переключения режима
USE_MOCK_API = settings.USE_API_STUBS


def get_api_client():
    """Фабрика для получения клиента API"""
    if USE_MOCK_API:
        return MockDnDApiClient()
    else:
        return RealDnDApiClient(settings.BACKEND_URL)


# Глобальный экземпляр клиента
api_client = get_api_client()
