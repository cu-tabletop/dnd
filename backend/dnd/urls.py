from ninja import Router

from .api import *

dnd_api = Router()

# urlpatterns = [
#     path('ping/', ping, name="ping"),
#     path('character/upload/', upload_character_view, name="upload character"),
#     path('character/get/', get_character_view, name='get character'),
#     path('campaign/create/', create_campaign_view, name='create campaign'),
#     path('campaign/get/', get_campaign_info_view, name='get campaign'),
#     path('campaign/add/', add_to_campaign_view, name='add to campaign'), # TODO: use params inside url
#     path('campaign/edit_permissions/', edit_permissions_view, name='edit permissions'), # TODO: use params inside url
#     path("ping/", ping_router),
#     path("character/", character_router),
#     path("campaign/", campaign_router),
# ]

dnd_api.add_router("ping/", ping_router)
dnd_api.add_router("character/", character_router)
dnd_api.add_router("campaign/", campaign_router)
