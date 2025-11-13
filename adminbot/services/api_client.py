import aiohttp
import logging
from typing import Optional, Dict, Any, List
import random
import asyncio

from ..settings import settings

logger = logging.getLogger(__name__)


class MockDnDApiClient:
    """Заглушка API для тестирования с расширенной функциональностью для персонажей"""

    def __init__(self):
        self.campaigns = [
            {
                "id": 1,
                "title": "Грифондор",
                "description": "Факультет храбрости и благородства",
                "icon": "🦁",
                "student_count": 5,
            },
            {
                "id": 2,
                "title": "Слизерин",
                "description": "Факультет амбициозных и хитрых",
                "icon": "🐍",
                "student_count": 4,
            },
        ]
        self.characters = [
            {
                "id": 1,
                "campaign_id": 1,
                "name": "Арагорн",
                "level": 6,
                "class": "⚔️ Воин",
                "race": "Человек",
                "player": "Игрок 1",
                "status": "активен",
                "hp_current": 45,
                "hp_max": 52,
                "xp": 1250,
                "last_activity": "15.01.2024",
                "data": {},
            },
            {
                "id": 2,
                "campaign_id": 1,
                "name": "Гэндальф",
                "level": 5,
                "class": "🧙‍♂️ Маг",
                "race": "Майар",
                "player": "Игрок 2",
                "status": "активен",
                "hp_current": 32,
                "hp_max": 32,
                "xp": 1100,
                "last_activity": "14.01.2024",
                "data": {},
            },
        ]
        self.next_campaign_id = 3
        self.next_character_id = 3

    async def ping(self) -> Dict[str, Any]:
        await self._simulate_delay()
        return {"message": "pong"}

    async def get_campaigns(
        self, user_id: Optional[int] = None, campaign_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        await self._simulate_delay()

        if campaign_id:
            return [camp for camp in self.campaigns if camp["id"] == campaign_id]
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
            "student_count": 0,
        }

        self.campaigns.append(new_campaign)
        self.next_campaign_id += 1

        return {
            "message": f"Кампания '{title}' создана успешно",
            "campaign": new_campaign,
        }

    async def get_campaign_characters(self, campaign_id: int) -> List[Dict[str, Any]]:
        """Получить персонажей кампании"""
        await self._simulate_delay()
        return [char for char in self.characters if char["campaign_id"] == campaign_id]

    async def get_character(self, char_id: int) -> Optional[Dict[str, Any]]:
        """Получить конкретного персонажа"""
        await self._simulate_delay()
        return next((char for char in self.characters if char["id"] == char_id), None)

    async def upload_character(
        self, owner_id: int, campaign_id: int, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Создать нового персонажа"""
        await self._simulate_delay()

        new_character = {
            "id": self.next_character_id,
            "owner_id": owner_id,
            "owner_telegram_id": owner_id,
            "campaign_id": campaign_id,
            "data": data,
            "name": data.get("name", "Безымянный"),
            "level": data.get("level", 1),
            "class": data.get("class", "⚔️ Воин"),
            "race": data.get("race", "Неизвестно"),
            "player": data.get("player", "Неизвестный игрок"),
            "status": "активен",
            "hp_current": data.get("hp_current", 10),
            "hp_max": data.get("hp_max", 10),
            "xp": data.get("xp", 0),
            "last_activity": "сегодня",
        }

        self.characters.append(new_character)
        self.next_character_id += 1

        return {
            "message": f"Персонаж '{new_character['name']}' создан",
            "character": new_character,
        }

    async def update_character(
        self, char_id: int, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обновить данные персонажа"""
        await self._simulate_delay()

        character = next(
            (char for char in self.characters if char["id"] == char_id), None
        )
        if character:
            character.update(data)
            character["data"].update(data)
            return {
                "message": f"Персонаж '{character['name']}' обновлен",
                "character": character,
            }
        return {"error": "Персонаж не найден"}

    async def _simulate_delay(self):
        """Имитация задержки сети"""
        await asyncio.sleep(random.uniform(0.1, 0.5))


class RealDnDApiClient:
    """Реальный клиент API"""

    def __init__(self, base_url: str):
        self.base_url = base_url

    async def ping(self) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/ping/") as response:
                return await response.json()

    async def get_campaigns(
        self, user_id: Optional[int] = None, campaign_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        try:
            params = {}
            if user_id:
                params["user_id"] = user_id
            if campaign_id:
                params["campaign_id"] = campaign_id

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/campaign/get/", params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list):
                            return data
                        else:
                            return [data]
                    else:
                        logger.error(f"API error getting campaigns: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error getting campaigns: {e}")
            return []

    async def create_campaign(
        self,
        telegram_id: int,
        title: str,
        description: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            payload = {
                "telegram_id": telegram_id,
                "title": title,
                "description": description,
                "icon": icon,
            }

            payload = {k: v for k, v in payload.items() if v is not None}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/campaign/create/", json=payload
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"API error creating campaign: {response.status} - {error_text}"
                        )
                        return {"error": f"Ошибка API: {response.status}"}
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            return {"error": f"Ошибка соединения: {str(e)}"}

    async def get_campaign_characters(self, campaign_id: int) -> List[Dict[str, Any]]:
        """Получить персонажей кампании через API"""
        try:
            # В реальном API нет прямого метода для получения персонажей кампании
            # Будем использовать обходной путь или вернем пустой список
            logger.warning("Метод get_campaign_characters не реализован в API")
            return []
        except Exception as e:
            logger.error(f"Error getting campaign characters: {e}")
            return []

    async def get_character(self, char_id: int) -> Optional[Dict[str, Any]]:
        """Получить конкретного персонажа через API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/character/get/", params={"char_id": char_id}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"API error getting character: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting character: {e}")
            return None

    async def upload_character(
        self, owner_id: int, campaign_id: int, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Создать нового персонажа через API"""
        try:
            payload = {"owner_id": owner_id, "campaign_id": campaign_id, "data": data}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/character/post/", json=payload
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"API error uploading character: {response.status} - {error_text}"
                        )
                        return {"error": f"Ошибка API: {response.status}"}
        except Exception as e:
            logger.error(f"Error uploading character: {e}")
            return {"error": f"Ошибка соединения: {str(e)}"}

    async def update_character(
        self, char_id: int, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обновить данные персонажа через API"""
        try:
            # В реальном API нет прямого метода обновления персонажа
            # Используем upload_character с существующим ID или возвращаем ошибку
            logger.warning("Метод update_character не реализован в API")
            return {"error": "Метод обновления персонажа не реализован в API"}
        except Exception as e:
            logger.error(f"Error updating character: {e}")
            return {"error": f"Ошибка соединения: {str(e)}"}


# Глобальная переменная для переключения режима
USE_MOCK_API = True


def get_api_client():
    """Фабрика для получения клиента API"""
    if USE_MOCK_API:
        return MockDnDApiClient()
    else:
        return RealDnDApiClient(settings.BACKEND_URL)  # Замените на ваш URL


# Глобальный экземпляр клиента
api_client = get_api_client()
