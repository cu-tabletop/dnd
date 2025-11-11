import base64
from io import BytesIO

from PIL import Image as PILImage
from django.core.files.base import ContentFile
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError
from ninja.responses import Response

from dnd.models import Campaign, CampaignMembership, Player
from dnd.schemas import (
    AddToCampaignRequest,
    CampaignEditPermissions,
    CampaignModelSchema,
    CreateCampaignRequest,
    ForbiddenError,
    Message,
    NotFoundError,
    ValidationError,
)

router = Router()


@router.post(
    "create/",
    response={
        201: Message,
        404: NotFoundError,
    },
)
def create_campaign_api(
    request: HttpRequest,
    campaign_request: CreateCampaignRequest,
):
    user_id = campaign_request.telegram_id
    user_obj = get_object_or_404(Player, telegram_id=user_id)

    campaign_title = campaign_request.title

    campaign_obj = Campaign.objects.create(
        title=campaign_title,
        verified=user_obj.verified,
    )

    if campaign_request.icon:
        decoded_icon = base64.b64decode(campaign_request.icon)
        image = PILImage.open(BytesIO(decoded_icon))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        campaign_obj.icon = ContentFile(buffer.read(), f"{campaign_title}.png")

    if campaign_request.description:
        campaign_obj.description = campaign_request.description

    campaign_obj.save()

    CampaignMembership.objects.create(
        user=user_obj,
        campaign=campaign_obj,
        status=2,
    )
    return 201, Message(message="created")


@router.get(
    "get/",
    response={
        200: CampaignModelSchema | list[CampaignModelSchema],
        404: NotFoundError,
    },
)
def get_campaign_info_api(
    request: HttpRequest,
    campaign_id: int | None = None,
    user_id: int | None = None,
):
    if campaign_id:
        campaign_obj = get_object_or_404(Campaign, id=campaign_id)

        if campaign_obj.private:
            if (
                not user_id
                or not CampaignMembership.objects.filter(
                    campaign=campaign_obj, user_id=user_id
                ).exists()
            ):
                # disguise private campaigns as non-existent
                raise HttpError(404, "requested campaign does not exist")

        return campaign_obj

    campaigns = Campaign.objects.filter(private=False)

    if user_id:
        user = Player.objects.get(telegram_id=user_id)
        user_campaigns = Campaign.objects.filter(
            id__in=CampaignMembership.objects.filter(
                user_id=user.id
            ).values_list("campaign_id", flat=True)
        )
        campaigns = campaigns.union(user_campaigns)

    return list(campaigns)


@router.post(
    "add/",
    response={
        200: str,
        201: str,
        403: ForbiddenError,
        404: NotFoundError,
    },
)
def add_to_campaign_api(
    request: HttpRequest,
    body: AddToCampaignRequest,
):
    campaign_obj = get_object_or_404(Campaign, id=body.campaign_id)

    # Verify owner permissions
    if not CampaignMembership.objects.filter(
        campaign=campaign_obj, user_id=body.owner_id, status=2
    ).exists():
        return 403, ForbiddenError(message="Only the owner can add members")

    user = get_object_or_404(Player, id=body.user_id)

    membership, created = CampaignMembership.objects.get_or_create(
        user=user, campaign=campaign_obj, defaults={"status": 0}
    )

    if not created:
        membership.status = 0
        membership.save()

    return Response(
        {"message": f"User {user.id} added to campaign {campaign_obj.id}"},
        status=201 if created else 200,
    )


@router.post(
    "edit-permissions/",
    response={
        200: Message,
        400: ValidationError,
        403: ValidationError,
        404: ValidationError,
    },
)
def edit_permissions_api(
    request: HttpRequest,
    body: CampaignEditPermissions,
):
    if body.status not in [0, 1, 2]:
        return 400, ValidationError(message="Invalid status value")

    campaign_obj = get_object_or_404(Campaign, id=body.campaign_id)

    # Verify owner permissions
    if not CampaignMembership.objects.filter(
        campaign=campaign_obj, user_id=body.owner_id, status=2
    ).exists():
        return 403, ForbiddenError(
            message="Only the owner can edit permissions"
        )

    membership = get_object_or_404(
        CampaignMembership,
        campaign=campaign_obj,
        user_id=body.user_id,
    )
    membership.status = body.status
    membership.save()

    return 200, Message(
        message=f"Updated user {body.user_id} role "
        f"to {body.status} in campaign {campaign_obj.id}"
    )
