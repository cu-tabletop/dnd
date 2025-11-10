from django.db import models

from dnd.models.campaign import Campaign
from dnd.models.character import Character
from dnd.models.player import Player
from dnd.models.room import Room


class RoomParticipation(models.Model):
    user = models.ForeignKey(Player, models.CASCADE)
    room = models.ForeignKey(Room, models.CASCADE)
    character = models.ForeignKey(Character, models.CASCADE)


class CampaignMembership(models.Model):
    ROLES = (
        (0, "Player"),
        (1, "Master"),
        (2, "Owner"),
    )

    user = models.ForeignKey(Player, models.CASCADE)
    campaign = models.ForeignKey(Campaign, models.CASCADE)
    status = models.PositiveSmallIntegerField(
        default=0,
        choices=ROLES,
    )  # Role. 0 - player, 1 - master, 2 - owner
