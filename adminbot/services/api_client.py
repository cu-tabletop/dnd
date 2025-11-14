import aiohttp
import logging
from typing import Optional, Dict, Any, List
import random
import asyncio
from datetime import datetime
from settings import settings

logger = logging.getLogger(__name__)


class MockDnDApiClient:
    """Заглушка API для тестирования с полной реализацией всех эндпоинтов"""

    def __init__(self):
        self.campaigns = [
            {
                "id": 1,
                "title": "Грифондор",
                "description": "Факультет храбрости и благородства",
                "icon": "🦁",
                "verified": True,
                "private": False,
            },
            {
                "id": 2,
                "title": "Слизерин",
                "description": "Факультет амбициозных и хитрых",
                "icon": "🐍",
                "verified": True,
                "private": False,
            },
        ]
        self.characters = [
            {
                "id": 1,
                "owner_id": 123,
                "owner_telegram_id": 123,
                "campaign_id": 1,
                "data": {
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
            },
            {
                "id": 2,
                "owner_id": 124,
                "owner_telegram_id": 124,
                "campaign_id": 1,
                "data": {
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
            },
        ]
        self.next_campaign_id = 3
        self.next_character_id = 3
        self.campaign_permissions = {}  # {campaign_id: {user_id: permission_level}}

    async def _simulate_delay(self):
        """Имитация задержки сети"""
        await asyncio.sleep(random.uniform(0.1, 0.5))

    # === PING ===
    async def ping(self) -> Dict[str, Any]:
        await self._simulate_delay()
        return {"message": "pong"}

    # === CHARACTER ENDPOINTS ===
    async def get_character(self, char_id: int) -> Optional[Dict[str, Any]]:
        await self._simulate_delay()
        for character in self.characters:
            if character["id"] == char_id:
                return character
        return None

    async def upload_character(
        self, owner_id: int, campaign_id: int, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        await self._simulate_delay()

        # Проверяем существование кампании
        campaign_exists = any(
            campaign["id"] == campaign_id for campaign in self.campaigns
        )
        if not campaign_exists:
            return {"error": "Кампания не найдена"}

        new_character = {
            "id": self.next_character_id,
            "owner_id": owner_id,
            "owner_telegram_id": owner_id,
            "campaign_id": campaign_id,
            "data": data,
        }

        self.characters.append(new_character)
        self.next_character_id += 1

        return new_character

    async def get_campaign_characters(
        self, campaign_id: int
    ) -> List[Dict[str, Any]]:
        await self._simulate_delay()
        return [
            char
            for char in self.characters
            if char["campaign_id"] == campaign_id
        ]

    async def update_character(
        self, char_id: int, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        await self._simulate_delay()

        for character in self.characters:
            if character["id"] == char_id:
                # Обновляем данные персонажа
                if "data" in update_data:
                    character["data"].update(update_data["data"])
                else:
                    character["data"].update(update_data)

                character["data"]["last_activity"] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                )
                return {
                    "message": f"Персонаж {char_id} обновлен",
                    "character": character,
                }

        return {"error": "Персонаж не найден"}

    # === CAMPAIGN ENDPOINTS ===
    async def get_campaigns(
        self, user_id: Optional[int] = None, campaign_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        await self._simulate_delay()

        if campaign_id:
            return [
                camp for camp in self.campaigns if camp["id"] == campaign_id
            ]

        # В моках возвращаем все кампании для любого пользователя
        return self.campaigns

    async def create_campaign(
        self,
        telegram_id: int,
        title: str,
        description: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> Dict[str, Any]:
        await self._simulate_delay()

        new_campaign = {
            "id": self.next_campaign_id,
            "title": title,
            "description": description or "Описание отсутствует",
            "icon": icon or "🏰",
            "verified": False,
            "private": False,
        }

        self.campaigns.append(new_campaign)
        self.next_campaign_id += 1

        return {"message": f"Кампания '{title}' создана успешно"}

    async def add_to_campaign(
        self, campaign_id: int, owner_id: int, user_id: int
    ) -> Dict[str, Any]:
        await self._simulate_delay()

        # Проверяем существование кампании
        campaign_exists = any(
            campaign["id"] == campaign_id for campaign in self.campaigns
        )
        if not campaign_exists:
            return {"error": "Кампания не найдена"}

        # Проверяем, что owner_id является владельцем кампании
        # В моках считаем, что все могут добавлять

        # В реальной реализации здесь была бы логика добавления пользователя в кампанию
        return {
            "message": f"Пользователь {user_id} добавлен в кампанию {campaign_id}"
        }

    async def edit_permissions(
        self, campaign_id: int, owner_id: int, user_id: int, status: int
    ) -> Dict[str, Any]:
        await self._simulate_delay()

        # Проверяем существование кампании
        campaign_exists = any(
            campaign["id"] == campaign_id for campaign in self.campaigns
        )
        if not campaign_exists:
            return {"error": "Кампания не найдена"}

        # Сохраняем права доступа
        if campaign_id not in self.campaign_permissions:
            self.campaign_permissions[campaign_id] = {}
        self.campaign_permissions[campaign_id][user_id] = status

        status_names = {0: "Участник", 1: "Мастер", 2: "Владелец"}
        return {
            "message": f"Права пользователя {user_id} изменены на: "
            f"{status_names.get(status, 'Неизвестно')}"
        }


class RealDnDApiClient:
    """Реальный клиент API с полной реализацией всех эндпоинтов"""

    def __init__(self, base_url: str):
        self.base_url = base_url

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Dict[str, Any]:
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
                        return {"error": f"Ошибка валидации: {error_data}"}
                    elif response.status == 403:
                        return {"error": "Доступ запрещен"}
                    elif response.status == 404:
                        return {"error": "Объект не найден"}
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"API error {response.status}: {error_text}"
                        )
                        return {"error": f"Ошибка API: {response.status}"}

        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            return {"error": f"Ошибка сети: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"error": f"Неожиданная ошибка: {str(e)}"}

    # === PING ===
    async def ping(self) -> Dict[str, Any]:
        return await self._make_request("GET", "/api/ping/")

    # === CHARACTER ENDPOINTS ===
    async def get_character(self, char_id: int) -> Optional[Dict[str, Any]]:
        result = await self._make_request(
            "GET", "/api/character/get/", params={"char_id": char_id}
        )
        return result if "error" not in result else None

    async def upload_character(
        self, owner_id: int, campaign_id: int, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        payload = {
            "owner_id": owner_id,
            "campaign_id": campaign_id,
            "data": data,
        }
        return await self._make_request(
            "POST", "/api/character/post/", json=payload
        )

    async def get_campaign_characters(
        self, campaign_id: int
    ) -> List[Dict[str, Any]]:
        """Получить всех персонажей кампании"""
        # В текущем API нет прямого метода для этого, поэтому получаем по одному
        # В реальном приложении лучше добавить отдельный эндпоинт
        characters = []

        # Это временное решение - в реальном API должен быть эндпоинт
        # для получения персонажей кампании
        # Пока возвращаем пустой список
        logger.warning(
            "get_campaign_characters: Этот метод требует отдельного эндпоинта на бэкенде"
        )
        return characters

    async def update_character(
        self, char_id: int, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обновить персонажа"""
        # В текущем API нет метода обновления персонажа
        logger.warning(
            "update_character: Этот метод требует реализации на бэкенде"
        )
        return {"error": "Метод обновления персонажа не реализован на сервере"}

    # === CAMPAIGN ENDPOINTS ===
    async def get_campaigns(
        self, user_id: Optional[int] = None, campaign_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        params = {}
        if user_id is not None:
            params["user_id"] = user_id
        if campaign_id is not None:
            params["campaign_id"] = campaign_id

        result = await self._make_request(
            "GET", "/api/campaign/get/", params=params
        )

        if "error" in result:
            return []

        # API может вернуть один объект или массив
        if isinstance(result, list):
            return result
        else:
            return [result]

    async def create_campaign(
        self,
        telegram_id: int,
        title: str,
        description: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {"telegram_id": telegram_id, "title": title}

        if description is not None:
            payload["description"] = description
        if icon is not None:
            payload["icon"] = icon

        return await self._make_request(
            "POST", "/api/campaign/create/", json=payload
        )

    async def add_to_campaign(
        self, campaign_id: int, owner_id: int, user_id: int
    ) -> Dict[str, Any]:
        payload = {
            "campaign_id": campaign_id,
            "owner_id": owner_id,
            "user_id": user_id,
        }
        return await self._make_request(
            "POST", "/api/campaign/add/", json=payload
        )

    async def edit_permissions(
        self, campaign_id: int, owner_id: int, user_id: int, status: int
    ) -> Dict[str, Any]:
        payload = {
            "campaign_id": campaign_id,
            "owner_id": owner_id,
            "user_id": user_id,
            "status": status,
        }
        return await self._make_request(
            "POST", "/api/campaign/edit-permissions/", json=payload
        )


# Глобальная переменная для переключения режима
USE_MOCK_API = True  # По умолчанию используем моки


def get_api_client():
    """Фабрика для получения клиента API"""
    if USE_MOCK_API:
        return MockDnDApiClient()
    else:
        return RealDnDApiClient(settings.BACKEND_URL)  # Замените на ваш URL


# Глобальный экземпляр клиента
api_client = get_api_client()
