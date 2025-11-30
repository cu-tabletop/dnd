from ninja import Router
from django.shortcuts import get_object_or_404
from typing import List
from datetime import datetime, timedelta

# import secrets

from dnd.models.invitation import Invitation
from dnd.models.campaign import Campaign
from dnd.models.player import Player
from dnd.models.character import Character
from dnd.models.participation import CampaignMembership
from dnd.schemas.invitation import (
    InvitationAcceptRequest,
    InvitationCreateRequest,
    InvitationResponse,
    InvitationByUsernameRequest,
)
from dnd.schemas.default import Message
from dnd.services.notification_service import notification_service

router = Router()


@router.post(
    "/create", response={200: InvitationResponse, 404: Message, 400: Message}
)
def create_invitation(request, data: InvitationCreateRequest):
    """Создание приглашения в кампанию"""
    try:
        campaign = get_object_or_404(Campaign, id=data.campaign_id)
        invited_by = get_object_or_404(
            Player, telegram_id=data.invited_by_telegram_id
        )
        invited_player = get_object_or_404(
            Player, telegram_id=data.invited_player_telegram_id
        )

        # Проверяем права - только мастер/владелец может приглашать
        membership = CampaignMembership.objects.filter(
            user=invited_by, campaign=campaign
        ).first()

        if not membership or membership.status == 0:  # 0 = player
            return 400, Message(message="Недостаточно прав для приглашения")

        # Проверяем, нет ли уже активного приглашения
        existing_invitation = Invitation.objects.filter(
            campaign=campaign,
            invited_player=invited_player,
            status="pending",
            expires_at__gte=datetime.now(),
        ).first()

        if existing_invitation:
            return 400, Message(
                message="У этого игрока уже есть активное приглашение"
            )

        # Создаем приглашение
        invitation = Invitation.objects.create(
            campaign=campaign,
            invited_player=invited_player,
            invited_by=invited_by,
            expires_at=datetime.now() + timedelta(days=7),
        )

        # Отправляем уведомление
        notification_service.send_invitation_notification(
            data.invited_player_telegram_id,
            {
                "id": invitation.id,
                "campaign_id": campaign.id,
                "campaign_title": campaign.title,
                "invited_player_telegram_id": invited_player.telegram_id,
                "invited_by_telegram_id": invited_by.telegram_id,
                "status": invitation.status,
                "expires_at": invitation.expires_at.isoformat(),
                "created_at": invitation.created_at.isoformat(),
            },
        )

        return 200, InvitationResponse(
            id=invitation.id,
            campaign_id=campaign.id,
            campaign_title=campaign.title,
            invited_player_telegram_id=invited_player.telegram_id,
            invited_by_telegram_id=invited_by.telegram_id,
            status=invitation.status,
            token=invitation.token,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
        )

    except Exception as e:
        return 400, Message(
            message=f"Ошибка при создании приглашения: {str(e)}"
        )


@router.post(
    "/create-by-username",
    response={200: InvitationResponse, 404: Message, 400: Message},
)
def create_invitation_by_username(request, data: InvitationByUsernameRequest):
    """Создание приглашения по username"""
    try:
        # Ищем игрока по username
        username = data.username.lstrip("@")
        invited_player = get_object_or_404(Player, telegram_username=username)

        # Создаем запрос для обычного создания приглашения
        invitation_data = InvitationCreateRequest(
            campaign_id=data.campaign_id,
            invited_player_telegram_id=invited_player.telegram_id,
            invited_by_telegram_id=data.invited_by_telegram_id,
        )

        return create_invitation(request, invitation_data)

    except Player.DoesNotExist:
        return 404, Message(message="Игрок с таким username не найден")
    except Exception as e:
        return 400, Message(message=f"Ошибка: {str(e)}")


@router.post("/accept", response={200: Message, 404: Message, 400: Message})
def accept_invitation(request, data: InvitationAcceptRequest):
    """Принятие приглашения с выбором персонажа"""
    try:
        invitation = get_object_or_404(Invitation, token=data.invitation_token)

        if invitation.status != "pending":
            return 400, Message(message="Приглашение уже обработано")

        if invitation.is_expired():
            invitation.status = "expired"
            invitation.save()
            return 400, Message(message="Приглашение просрочено")

        character = get_object_or_404(
            Character, id=data.character_id, owner=invitation.invited_player
        )

        # Добавляем персонажа в кампанию (обновляем связь)
        character.campaign = invitation.campaign
        character.save()

        # Создаем запись участия игрока в кампании
        CampaignMembership.objects.get_or_create(
            user=invitation.invited_player,
            campaign=invitation.campaign,
            defaults={"status": 0},  # 0 = player
        )

        invitation.status = "accepted"
        invitation.save()

        # Уведомляем мастера
        notification_service.send_invitation_accepted_notification(
            invitation.invited_by.telegram_id,
            {
                "campaign_title": invitation.campaign.title,
                "player_telegram_id": invitation.invited_player.telegram_id,
                "player_username": invitation.invited_player.telegram_username,
                "character_name": character.get("info", "name")
                or "Неизвестный персонаж",
                "accepted_at": datetime.now().isoformat(),
            },
        )

        return 200, Message(message="Вы успешно присоединились к кампании")

    except Exception as e:
        return 400, Message(
            message=f"Ошибка при принятии приглашения: {str(e)}"
        )


@router.get("/pending/{telegram_id}", response=List[InvitationResponse])
def get_pending_invitations(request, telegram_id: int):
    """Получение ожидающих приглашений для игрока"""
    player = get_object_or_404(Player, telegram_id=telegram_id)
    invitations = Invitation.objects.filter(
        invited_player=player, status="pending", expires_at__gte=datetime.now()
    ).select_related("campaign", "invited_by")

    return [
        InvitationResponse(
            id=inv.id,
            campaign_id=inv.campaign.id,
            campaign_title=inv.campaign.title,
            invited_player_telegram_id=player.telegram_id,
            invited_by_telegram_id=inv.invited_by.telegram_id,
            status=inv.status,
            token=inv.token,
            expires_at=inv.expires_at,
            created_at=inv.created_at,
        )
        for inv in invitations
    ]
