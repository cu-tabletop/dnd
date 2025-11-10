from ninja import Router

from .api import *

dnd_api = Router()

dnd_api.add_router("ping/", ping_router)
dnd_api.add_router("character/", character_router)
dnd_api.add_router("campaign/", campaign_router)
dnd_api.add_router("player/", player_router)
