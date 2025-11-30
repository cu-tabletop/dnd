import aiohttp
import logging
from typing import Optional, Union
from settings import settings
from .models import (
    AddInventoryItemResponse,
    CampaignModelSchema,
    CreateCampaignResponse,
    DeleteInventoryItemResponse,
    ErrorResponse,
    GetCharacterResponse,
    InventoryItem,
    InventoryItemCreate,
    InventoryItemUpdate,
    InvitationResponse,
    Message,
    PlayerResponse,
    UpdateInventoryItemResponse,
    UploadCharacterResponse,
)

logger = logging.getLogger(__name__)


class ApiError(Exception):
    pass


class ValidationError(ApiError):
    pass


class NotFoundError(ApiError):
    pass


class ForbiddenError(ApiError):
    pass


class RealDnDApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Union[dict, list]:
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

    # === PLAYER METHODS ===
    async def search_players(
        self, username: Optional[str] = None, telegram_id: Optional[int] = None
    ) -> list[PlayerResponse]:
        result = await self._make_request(
            "POST",
            "/api/players/search",
            json={"username": username, "telegram_id": telegram_id},
        )
        return [PlayerResponse(**item) for item in result]

    async def update_player_info(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> PlayerResponse:
        result = await self._make_request(
            "POST",
            "/api/players/update-info",
            json={
                "telegram_id": telegram_id,
                "telegram_username": username,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
        return PlayerResponse(**result)

    # === INVITATION METHODS ===
    async def create_invitation_by_username(
        self, campaign_id: int, username: str, invited_by_telegram_id: int
    ) -> InvitationResponse:
        result = await self._make_request(
            "POST",
            "/api/invitations/create-by-username",
            json={
                "campaign_id": campaign_id,
                "username": username,
                "invited_by_telegram_id": invited_by_telegram_id,
            },
        )
        return InvitationResponse(**result)

    async def get_pending_invitations(
        self, telegram_id: int
    ) -> list[InvitationResponse]:
        result = await self._make_request(
            "GET", f"/api/invitations/pending/{telegram_id}"
        )
        return [InvitationResponse(**item) for item in result]

    async def accept_invitation(
        self, invitation_token: str, character_id: int
    ) -> Message:
        result = await self._make_request(
            "POST",
            "/api/invitations/accept",
            json={
                "invitation_token": invitation_token,
                "character_id": character_id,
            },
        )
        return Message(**result)

    # === CAMPAIGN METHODS ===
    async def get_campaigns(self, user_id: int) -> list[CampaignModelSchema]:
        result = await self._make_request(
            "GET", "/api/campaign/get/", params={"user_id": user_id}
        )
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
        result = await self._make_request(
            "POST",
            "/api/campaign/create/",
            json={
                "telegram_id": telegram_id,
                "title": title,
                "description": description,
                "icon": icon,
            },
        )
        return CreateCampaignResponse(**result)

    # === CHARACTER METHODS ===
    async def get_campaign_characters(
        self, campaign_id: int
    ) -> list[GetCharacterResponse]:
        # Получаем всех персонажей и фильтруем по кампании
        characters = []
        # Временная реализация - в будущем нужно добавить отдельный эндпоинт
        campaign = await self._make_request(
            "GET", "/api/campaign/get/", params={"campaign_id": campaign_id}
        )
        if campaign:
            # Здесь логика получения персонажей кампании
            pass
        return characters

    async def get_character(
        self, character_id: int
    ) -> Optional[GetCharacterResponse]:
        result = await self._make_request(
            "GET", "/api/character/get/", params={"char_id": character_id}
        )
        return GetCharacterResponse(**result) if result else None

    async def update_character(
        self, character_id: int, update_data: dict
    ) -> Union[GetCharacterResponse, ErrorResponse]:
        try:
            # Получаем текущего персонажа
            current_char = await self.get_character(character_id)
            if not current_char:
                return ErrorResponse(error="Персонаж не найден")

            # Обновляем данные
            updated_data = {**current_char.data, **update_data}

            # Создаем нового персонажа с обновленными данными
            new_char = await self.upload_character(
                owner_id=current_char.owner_id,
                campaign_id=current_char.campaign_id,
                data=updated_data,
            )

            if isinstance(new_char, ErrorResponse):
                return new_char
            return GetCharacterResponse(**new_char.dict())
        except Exception as e:
            return ErrorResponse(error=str(e))

    async def upload_character(
        self, owner_id: int, campaign_id: int, data: dict
    ) -> Union[UploadCharacterResponse, ErrorResponse]:
        result = await self._make_request(
            "POST",
            "/api/character/post/",
            json={
                "owner_id": owner_id,
                "campaign_id": campaign_id,
                "data": data,
            },
        )
        return UploadCharacterResponse(**result)

    # === INVENTORY METHODS ===
    async def get_character_inventory(
        self, character_id: int
    ) -> list[InventoryItem]:
        character = await self.get_character(character_id)
        if not character:
            return []

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

    async def add_inventory_item(
        self, character_id: int, item: InventoryItemCreate
    ) -> Union[AddInventoryItemResponse, ErrorResponse]:
        try:
            character = await self.get_character(character_id)
            if not character:
                return ErrorResponse(error="Персонаж не найден")

            current_data = character.data
            inventory = current_data.get("inventory", [])

            new_item = {
                "name": item.name,
                "description": item.description,
                "quantity": item.quantity,
            }
            inventory.append(new_item)

            updated_data = {**current_data, "inventory": inventory}
            result = await self.update_character(character_id, updated_data)

            if isinstance(result, ErrorResponse):
                return result

            new_item_id = len(inventory)
            return AddInventoryItemResponse(
                id=new_item_id,
                character_id=character_id,
                name=item.name,
                description=item.description,
                quantity=item.quantity,
            )
        except Exception as e:
            return ErrorResponse(error=str(e))

    async def update_inventory_item(
        self, character_id: int, item_id: int, update_data: InventoryItemUpdate
    ) -> Union[UpdateInventoryItemResponse, ErrorResponse]:
        try:
            character = await self.get_character(character_id)
            if not character:
                return ErrorResponse(error="Персонаж не найден")

            current_data = character.data
            inventory = current_data.get("inventory", [])

            updated_item = [
                item for item in inventory if item.get("id", 0) == item_id
            ][0]
            updated_item.update(update_data.model_dump())

            inventory = [
                item if item.get("id", 0) != item_id else updated_item
                for item in inventory
            ]

            updated_data = {**current_data, "inventory": inventory}
            result = await self.update_character(character_id, updated_data)

            if isinstance(result, ErrorResponse):
                return result

            return UpdateInventoryItemResponse(
                id=item_id,
                character_id=character_id,
                name=updated_item["name"],
                description=updated_item["description"],
                quantity=updated_item["quantity"],
            )
        except Exception as e:
            return ErrorResponse(error=str(e))

    async def delete_inventory_item(
        self, character_id: int, item_id: int
    ) -> Union[DeleteInventoryItemResponse, ErrorResponse]:
        try:
            character = await self.get_character(character_id)
            if not character:
                return ErrorResponse(error="Персонаж не найден")

            current_data = character.data
            inventory = current_data.get("inventory", [])

            inventory = [
                item for item in inventory if item.get("id", 0) != item_id
            ]

            updated_data = {**current_data, "inventory": inventory}
            result = await self.update_character(character_id, updated_data)

            if isinstance(result, ErrorResponse):
                return result

            return DeleteInventoryItemResponse(
                message="Предмет успешно удалён"
            )
        except Exception as e:
            return ErrorResponse(error=str(e))


# Глобальный экземпляр клиента
api_client = RealDnDApiClient(settings.BACKEND_URL)
