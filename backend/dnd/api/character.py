from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.responses import Response

from dnd.models import Campaign, Character, Player
from dnd.schemas.character import CharacterOut, UploadCharacter
from dnd.schemas.error import NotFoundError, ValidationError, ForbiddenError

router = Router()


@router.get(
    "/get/",
    response={
        200: CharacterOut,
        400: ValidationError,
        404: NotFoundError,
    },
)
def get_character_api(request: HttpRequest, char_id: int) -> Response:
    char_obj = get_object_or_404(Character, id=char_id)

    return CharacterOut(
        id=char_obj.id,
        owner_id=char_obj.owner_id,
        owner_telegram_id=char_obj.owner.telegram_id,
        data=char_obj.load_data(),
        campaign_id=char_obj.campaign_id,
    )


@router.post(
    "post/",
    response={
        201: CharacterOut,
        400: ValidationError,
        404: NotFoundError,
    },
)
def upload_character_api(request: HttpRequest, upload: UploadCharacter):
    owner_obj = get_object_or_404(Player, id=upload.owner_id)

    campaign_obj = get_object_or_404(Campaign, id=upload.campaign_id)

    char_obj = Character.objects.create(owner=owner_obj, campaign=campaign_obj)
    char_obj.save_data(upload.data)

    return 201, CharacterOut(
        id=char_obj.id,
        owner_id=char_obj.owner_id,
        owner_telegram_id=char_obj.owner.telegram_id,
        data=char_obj.load_data(),
        campaign_id=char_obj.campaign_id,
    )
