import functools
import logging
import aiohttp
from typing import Callable, List
from settings import settings
from models.models import (
    CharacterShort,
    Company,
    Character,
    CharacterDetail,
    CompanyCreate,
    InventoryItem,
    InventoryItemUpdate,
)
from services.stub_api_client import StubAPIClient


def log_rating_operations(func: Callable) -> Callable:
    """Декоратор для логирования операций с рейтингом"""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        try:
            character_id = kwargs.get("character_id") or (
                args[1] if len(args) > 1 else None
            )
            rating = kwargs.get("rating") or (args[2] if len(args) > 2 else None)

            logger.info(
                f"Rating operation: {func.__name__}, character_id: {character_id}, "
                f"new_rating: {rating}"
            )
            result = await func(*args, **kwargs)
            logger.info(
                f"Rating operation successful: {func.__name__}, "
                f"character_id: {character_id}"
            )
            return result
        except Exception as e:
            logger.error(f"Rating operation failed: {func.__name__}, error: {e}")
            raise

    return wrapper


def log_inventory_operation(operation: str):
    """Декоратор для логирования операций с инвентарем"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            try:
                character_id = kwargs.get("character_id")
                item_data = kwargs.get("item_data") or kwargs.get("item")

                logger.info(
                    f"Inventory {operation}: character_id={character_id}, "
                    f"item={getattr(item_data, 'name', 'Unknown')}"
                )
                result = await func(*args, **kwargs)
                logger.info(f"Inventory {operation} successful")
                return result
            except Exception as e:
                logger.error(f"Inventory {operation} failed: {e}")
                raise

        return wrapper

    return decorator


class APIClient:
    def __init__(self):
        self.base_url = settings.BACKEND_URL
        self.logger = logging.getLogger(__name__)

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        url = f"{self.base_url}/{endpoint}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, **kwargs) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            self.logger.error(f"API request failed: {e}")
            raise

    async def get_companies(self) -> List[Company]:
        data = await self._make_request("GET", "companies")
        return [Company(**item) for item in data]

    async def get_company_characters(self, company_id: int) -> List[Character]:
        data = await self._make_request("GET", f"companies/{company_id}/characters")
        return [Character(**item) for item in data]

    async def get_character(self, character_id: int) -> CharacterDetail:
        data = await self._make_request("GET", f"characters/{character_id}")
        return CharacterDetail(**data)

    async def update_character_level(self, character_id: int, level: int) -> Character:
        data = await self._make_request(
            "PATCH", f"characters/{character_id}", json={"level": level}
        )
        return Character(**data)

    async def add_inventory_item(
        self, character_id: int, item: InventoryItem
    ) -> InventoryItem:
        data = await self._make_request(
            "POST", f"characters/{character_id}/inventory", json=item.dict()
        )
        return InventoryItem(**data)

    async def delete_inventory_item(self, item_id: int) -> bool:
        await self._make_request("DELETE", f"inventory/{item_id}")
        return True

    async def get_character_jpeg(self, character_id: int) -> bytes:
        url = f"{self.base_url}/characters/{character_id}/export/jpeg"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.read()

    @log_rating_operations
    async def update_character_rating(
        self, character_id: int, rating: int
    ) -> Character:
        """Обновление рейтинга персонажа"""
        data = await self._make_request(
            "PATCH", f"characters/{character_id}", json={"rating": rating}
        )
        return Character(**data)

    async def get_character_inventory(self, character_id: int) -> List[InventoryItem]:
        """Получение инвентаря персонажа"""
        data = await self._make_request("GET", f"characters/{character_id}/inventory")
        return [InventoryItem(**item) for item in data]

    async def update_inventory_item(
        self, item_id: int, item_data: InventoryItemUpdate
    ) -> InventoryItem:
        """Обновление предмета инвентаря"""
        data = await self._make_request(
            "PATCH", f"inventory/{item_id}", json=item_data.dict(exclude_unset=True)
        )
        return InventoryItem(**data)

    async def get_user_companies(self, user_id: int) -> List[Company]:
        """Получение компаний пользователя"""
        data = await self._make_request("GET", f"users/{user_id}/companies")
        return [Company(**item) for item in data]

    async def create_company(
        self, user_id: int, company_data: CompanyCreate
    ) -> Company:
        """Создание новой компании"""
        data = await self._make_request(
            "POST", f"users/{user_id}/companies", json=company_data.dict()
        )
        return Company(**data)

    async def delete_company(self, company_id: int) -> bool:
        """Удаление компании"""
        await self._make_request("DELETE", f"companies/{company_id}")
        return True

    async def add_master_to_company(
        self, company_id: int, master_username: str
    ) -> bool:
        """Добавление мастера в компанию"""
        await self._make_request(
            "POST",
            f"companies/{company_id}/masters",
            json={"username": master_username},
        )
        return True

    async def get_company_characters_short(
        self, company_id: int
    ) -> List[CharacterShort]:
        """Получение краткого списка персонажей компании"""
        data = await self._make_request(
            "GET", f"companies/{company_id}/characters/short"
        )
        return [CharacterShort(**item) for item in data]


def get_api_client():
    if settings.USE_API_STUBS:
        return StubAPIClient()
    else:
        return APIClient()
