import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any, List
from settings import settings

import random

logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


class MockDnDApiClient:
    """Заглушка API для тестирования"""

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
            {
                "id": 3,
                "title": "Когтевран",
                "description": "Факультет мудрых и любознательных",
                "icon": "🦅",
                "student_count": 6,
            },
            {
                "id": 4,
                "title": "Пуффендуй",
                "description": "Факультет верных и трудолюбивых",
                "icon": "🦡",
                "student_count": 3,
            },
        ]
        self.next_id = 5

    async def ping(self) -> Dict[str, Any]:
        await self._simulate_delay()
        return {"message": "pong"}

    async def get_campaigns(
        self, user_id: Optional[int] = None, campaign_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        await self._simulate_delay()

        if campaign_id:
            return [camp for camp in self.campaigns if camp["id"] == campaign_id]

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
            "id": self.next_id,
            "title": title,
            "description": description or "Описание отсутствует",
            "icon": icon or "🏰",
            "student_count": 0,
        }

        self.campaigns.append(new_campaign)
        self.next_id += 1

        return {
            "message": f"Кампания '{title}' создана успешно",
            "campaign": new_campaign,
        }

    async def add_to_campaign(
        self, campaign_id: int, owner_id: int, user_id: int
    ) -> Dict[str, Any]:
        await self._simulate_delay()
        return {"message": f"Пользователь {user_id} добавлен в кампанию {campaign_id}"}

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
                        logger.error(f"API error: {response.status}")
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
                            f"API error creating campaign: {response.status} - "
                            f"{error_text}"
                        )
                        return {"error": f"Ошибка API: {response.status}"}
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            return {"error": f"Ошибка соединения: {str(e)}"}

    async def add_to_campaign(
        self, campaign_id: int, owner_id: int, user_id: int
    ) -> Dict[str, Any]:
        try:
            payload = {
                "campaign_id": campaign_id,
                "owner_id": owner_id,
                "user_id": user_id,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/campaign/add/", json=payload
                ) as response:
                    if response.status in [200, 201]:
                        return await response.json()
                    else:
                        logger.error(f"API error adding to campaign: {response.status}")
                        return {"error": f"API error: {response.status}"}
        except Exception as e:
            logger.error(f"Error adding to campaign: {e}")
            return {"error": str(e)}


# Глобальная переменная для переключения режима
USE_MOCK_API = True  # По умолчанию используем моки


def get_api_client():
    """Фабрика для получения клиента API"""
    if USE_MOCK_API:
        return MockDnDApiClient()
    else:
        return RealDnDApiClient(settings.BACKEND_URL)


# Глобальный экземпляр клиента
api_client = get_api_client()
