from ninja import Router

# from django.shortcuts import get_object_or_404
from dnd.models.player import Player
from dnd.schemas.player import (
    PlayerResponse,
    PlayerSearchSchema,
    PlayerUpdateRequest,
)
from dnd.schemas.default import Message

router = Router()


@router.post("/search", response=list[PlayerResponse])
def search_players(request, data: PlayerSearchSchema):
    """Поиск игроков по telegram_id или username"""
    players = Player.objects.all()

    if data.telegram_id:
        players = players.filter(telegram_id=data.telegram_id)

    if data.username:
        username = data.username.lstrip("@").lower()
        players = players.filter(telegram_username__iexact=username)

    return [
        PlayerResponse(
            id=player.id,
            telegram_id=player.telegram_id,
            telegram_username=player.telegram_username,
            first_name=player.first_name,
            last_name=player.last_name,
        )
        for player in players
    ]


@router.post("/update-info", response={200: PlayerResponse, 404: Message})
def update_player_info(request, data: PlayerUpdateRequest):
    """Обновление информации об игроке"""
    player, created = Player.objects.update_or_create(
        telegram_id=data.telegram_id,
        defaults={
            "telegram_username": data.telegram_username,
            "first_name": data.first_name,
            "last_name": data.last_name,
        },
    )

    return 200, PlayerResponse(
        id=player.id,
        telegram_id=player.telegram_id,
        telegram_username=player.telegram_username,
        first_name=player.first_name,
        last_name=player.last_name,
    )
