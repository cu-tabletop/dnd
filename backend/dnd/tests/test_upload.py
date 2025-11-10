import json

from django.urls import reverse
from rest_framework.test import APITestCase

from ..models import *


class TestUploadCharacter(APITestCase):
    def test_upload_character_success(self):
        url = reverse("api-1.0.0:upload_character_api")
        data_obj = json.load(
            open("dnd/tests/example-character.json", encoding="utf-8")
        )
        user_id = 1
        campaign_obj = Campaign.objects.create(title="test campaign")
        player_obj = Player.objects.create(
            id=user_id,
            telegram_id=123,
            bio="test bio",
            admin=False,
        )
        CampaignMembership.objects.create(
            user=player_obj,
            campaign=campaign_obj,
        )
        self.assertEqual(Character.objects.all().count(), 0)
        response = self.client.post(
            url,
            data={
                "owner_id": user_id,
                "campaign_id": campaign_obj.id,
                "data": data_obj,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Character.objects.all().count(), 1)
