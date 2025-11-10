import base64
from PIL import Image as PILImage
from django.core.files.base import ContentFile
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from io import BytesIO
from ninja import Router
from ninja.errors import HttpError
from ninja.responses import Response

from ..models import Campaign, CampaignMembership, Player
from ..schemas import (
    AddToCampaignRequest,
    CampaignEditPermissions,
    CampaignModelSchema,
    CreateCampaignRequest,
    ForbiddenError,
    Message,
    NotFoundError,
    ValidationError,
)
from ..schemas.player import RegisterRequest

router = Router()

@router.post(
    path="register/",
    response={
        200: Message,
        201: Message,
    }
)
def register_player(request: HttpRequest, player_request: RegisterRequest):
    _, created = Player.objects.update_or_create(telegram_id=player_request.telegram_id, defaults=player_request.dict())
    if not created:
        return 200, Message(message="Player was already created")
    return 201, Message(message="Player created successfully")
