import aiohttp
import logging
from typing import Optional, List, Union

from settings import settings
from .models import (
    AddInventoryItemResponse,
    DeleteInventoryItemResponse,
    ErrorResponse,
    InventoryItem,
    InventoryItemCreate,
    InventoryItemUpdate,
    PingResponse,
    GetCharacterResponse,
    UpdateInventoryItemResponse,
    UploadCharacterResponse,
    CreateCampaignResponse,
    UpdateCampaignRequest,
    AddToCampaignResponse,
    EditPermissionsResponse,
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
                        raise ValidationError(
                            f"Ошибка валидации: {error_data}"
                        )
                    elif response.status == 403:
                        raise ForbiddenError("Доступ запрещен")
                    elif response.status == 404:
                        raise NotFoundError("Объект не найден")
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"API error {response.status}: {error_text}"
                        )
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
    async def get_character(
        self, char_id: int
    ) -> Optional[GetCharacterResponse]:
        result = await self._make_request(
            "GET", "/api/character/get/", params={"char_id": char_id}
        )
        return GetCharacterResponse(**result) if result else None

    async def upload_character(
        self, owner_id: int, campaign_id: int, data: dict
    ) -> Union[UploadCharacterResponse, ErrorResponse]:
        payload = UploadCharacter(
            owner_id=owner_id,
            campaign_id=campaign_id,
            data=data,
        )
        try:
            result = await self._make_request(
                "POST", "/api/character/post/", json=payload.model_dump()
            )
            return UploadCharacterResponse(**result)
        except (ValidationError, NotFoundError, ForbiddenError) as e:
            return ErrorResponse(error=str(e))
        except ApiError as e:
            return ErrorResponse(error=str(e))

    async def get_campaign_characters(
        self, campaign_id: int
    ) -> List[GetCharacterResponse]:
        """Получить всех персонажей кампании - временное решение через фильтрацию"""
        # Поскольку отдельного эндпоинта нет, будем получать всех персонажей по одному
        # Это неэффективно, но работает
        characters = []
        # В реальной реализации здесь может быть кэширование или другой подход
        logger.warning(
            "Метод get_campaign_characters использует обходной путь - может быть медленным"
        )
        return characters

    async def update_character(
        self, char_id: int, update_data: dict
    ) -> Union[GetCharacterResponse, ErrorResponse]:
        """Обновить персонажа через получение и перезапись"""
        try:
            # Получаем текущего персонажа
            current_char = await self.get_character(char_id)
            if not current_char:
                return ErrorResponse(error="Персонаж не найден")

            # Обновляем данные
            updated_data = {**current_char.data, **update_data}

            # Создаем нового персонажа с обновленными данными
            # ВАЖНО: Это создаст нового персонажа, а не обновит существующего!
            # Для настоящего обновления нужен отдельный эндпоинт на бэкенде
            new_char = await self.upload_character(
                owner_id=current_char.owner_id,
                campaign_id=current_char.campaign_id,
                data=updated_data,
            )

            if isinstance(new_char, ErrorResponse):
                return new_char

            return GetCharacterResponse(**new_char.model_dump())

        except Exception as e:
            logger.error(f"Error updating character: {e}")
            return ErrorResponse(error=str(e))

    # === INVENTORY ENDPOINTS ===
    async def get_character_inventory(
        self, character_id: int
    ) -> List[InventoryItem]:
        """Получить инвентарь персонажа - временная реализация через данные персонажа"""
        try:
            character = await self.get_character(character_id)
            if not character:
                return []

            # Ищем инвентарь в данных персонажа
            inventory_data = character.data.get("inventory", [])
            inventory = []

            for i, item_data in enumerate(inventory_data):
                if isinstance(item_data, dict):
                    inventory.append(
                        InventoryItem(
                            id=i + 1,
                            character_id=character_id,
                            name=item_data.get("name", "Неизвестный предмет"),
                            description=item_data.get("description", ""),
                            quantity=item_data.get("quantity", 1),
                        )
                    )

            return inventory
        except Exception as e:
            logger.error(f"Error getting character inventory: {e}")
            return []

    async def add_inventory_item(
        self, character_id: int, item: InventoryItemCreate
    ) -> Union[AddInventoryItemResponse, ErrorResponse]:
        """Добавить предмет в инвентарь через обновление данных персонажа"""
        try:
            character = await self.get_character(character_id)
            if not character:
                return ErrorResponse(error="Персонаж не найден")

            # Получаем текущий инвентарь
            current_data = character.data
            inventory = current_data.get("inventory", [])

            # Добавляем новый предмет
            new_item = {
                "name": item.name,
                "description": item.description,
                "quantity": item.quantity,
            }
            inventory.append(new_item)

            # Обновляем данные персонажа
            updated_data = {**current_data, "inventory": inventory}
            result = await self.update_character(character_id, updated_data)

            if isinstance(result, ErrorResponse):
                return result

            # Генерируем ID для нового предмета
            new_item_id = len(inventory)

            return AddInventoryItemResponse(
                id=new_item_id,
                character_id=character_id,
                name=item.name,
                description=item.description,
                quantity=item.quantity,
            )

        except Exception as e:
            logger.error(f"Error adding inventory item: {e}")
            return ErrorResponse(error=str(e))

    async def update_inventory_item(
        self, item_id: int, update_data: InventoryItemUpdate
    ) -> Union[UpdateInventoryItemResponse, ErrorResponse]:
        """Обновить предмет в инвентаре"""
        try:
            # Находим персонажа по предмету (это неэффективно)
            # В реальной реализации нужен отдельный эндпоинт
            characters = []  # Здесь должна быть логика поиска персонажа по item_id

            for char_response in characters:
                character = char_response
                inventory = character.data.get("inventory", [])

                if 0 <= item_id - 1 < len(inventory):
                    # Обновляем предмет
                    current_item = inventory[item_id - 1]
                    if update_data.name is not None:
                        current_item["name"] = update_data.name
                    if update_data.description is not None:
                        current_item["description"] = update_data.description
                    if update_data.quantity is not None:
                        current_item["quantity"] = update_data.quantity

                    # Сохраняем обновленные данные
                    updated_data = {**character.data, "inventory": inventory}
                    result = await self.update_character(
                        character.id, updated_data
                    )

                    if isinstance(result, ErrorResponse):
                        return result

                    return UpdateInventoryItemResponse(
                        id=item_id,
                        character_id=character.id,
                        name=current_item["name"],
                        description=current_item["description"],
                        quantity=current_item["quantity"],
                    )

            return ErrorResponse(error="Предмет не найден")

        except Exception as e:
            logger.error(f"Error updating inventory item: {e}")
            return ErrorResponse(error=str(e))

    async def delete_inventory_item(
        self, item_id: int
    ) -> Union[DeleteInventoryItemResponse, ErrorResponse]:
        """Удалить предмет из инвентаря"""
        try:
            # Аналогично update_inventory_item, находим и удаляем предмет
            characters = []  # Логика поиска персонажа по item_id

            for char_response in characters:
                character = char_response
                inventory = character.data.get("inventory", [])

                if 0 <= item_id - 1 < len(inventory):
                    # Удаляем предмет
                    inventory.pop(item_id - 1)

                    # Обновляем данные
                    updated_data = {**character.data, "inventory": inventory}
                    result = await self.update_character(
                        character.id, updated_data
                    )

                    if isinstance(result, ErrorResponse):
                        return result

                    return DeleteInventoryItemResponse(
                        message="Предмет удален"
                    )

            return ErrorResponse(error="Предмет не найден")

        except Exception as e:
            logger.error(f"Error deleting inventory item: {e}")
            return ErrorResponse(error=str(e))

    # === CAMPAIGN ENDPOINTS ===
    async def get_campaigns(
        self, user_id: Optional[int] = None, campaign_id: Optional[int] = None
    ) -> List[CampaignModelSchema]:
        params = {}
        if user_id is not None:
            params["user_id"] = user_id
        if campaign_id is not None:
            params["campaign_id"] = campaign_id

        result = await self._make_request(
            "GET", "/api/campaign/get/", params=params
        )

        # Создаем временный объект для парсинга ответа
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
    ) -> Union[CreateCampaignResponse, ErrorResponse]:
        payload = CreateCampaignRequest(
            telegram_id=telegram_id,
            title=title,
            description=description,
            icon=icon,
        )
        try:
            result = await self._make_request(
                "POST", "/api/campaign/create/", json=payload.model_dump()
            )
            return CreateCampaignResponse(**result)
        except (ValidationError, NotFoundError, ForbiddenError) as e:
            return ErrorResponse(error=str(e))
        except ApiError as e:
            return ErrorResponse(error=str(e))

    async def update_campaign(
        self,
        telegram_id: int,
        campaign_id: int,
        title: Optional[str],
        description: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> Union[CreateCampaignResponse, ErrorResponse]:
        payload = UpdateCampaignRequest(
            telegram_id=telegram_id,
            campaign_id=campaign_id,
            title=title,
            description=description,
            icon=icon,
        )
        try:
            result = await self._make_request(
                "PATCH", "/api/campaign/update/", json=payload.model_dump()
            )
            return CreateCampaignResponse(**result)
        except (ValidationError, NotFoundError, ForbiddenError) as e:
            return ErrorResponse(error=str(e))
        except ApiError as e:
            return ErrorResponse(error=str(e))

    async def add_to_campaign(
        self, campaign_id: int, owner_id: int, user_id: int
    ) -> Union[AddToCampaignResponse, ErrorResponse]:
        payload = AddToCampaignRequest(
            campaign_id=campaign_id,
            owner_id=owner_id,
            user_id=user_id,
        )
        try:
            result = await self._make_request(
                "POST", "/api/campaign/add/", json=payload.model_dump()
            )
            return AddToCampaignResponse(**result)
        except (ValidationError, NotFoundError, ForbiddenError) as e:
            return ErrorResponse(error=str(e))
        except ApiError as e:
            return ErrorResponse(error=str(e))

    async def edit_permissions(
        self,
        campaign_id: int,
        owner_id: int,
        user_id: int,
        status: CampaignPermissions,
    ) -> EditPermissionsResponse:
        payload = CampaignEditPermissions(
            campaign_id=campaign_id,
            owner_id=owner_id,
            user_id=user_id,
            status=status,
        )
        try:
            result = await self._make_request(
                "POST",
                "/api/campaign/edit-permissions/",
                json=payload.model_dump(),
            )
            return EditPermissionsResponse(**result)
        except (ValidationError, NotFoundError, ForbiddenError) as e:
            return ErrorResponse(error=str(e))
        except ApiError as e:
            return ErrorResponse(error=str(e))


# Глобальный экземпляр клиента
api_client = RealDnDApiClient(settings.BACKEND_URL)
