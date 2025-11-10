from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APITestCase, APIClient

from ..models import *


class TestGetCharacter(APITestCase):
    client: APIClient

    def test_get_character_success(self):
        url = reverse("api-1.0.0:get_character_api")

        owner_obj = Player.objects.create(telegram_id=1, bio="test bio")
        campaign_obj = Campaign.objects.create(title="test")
        char_obj = Character.objects.create(
            owner=owner_obj, campaign=campaign_obj
        )
        char_data = {
            "char_name": "Grigory",
        }
        char_obj.save_data(char_data)
        char_obj.save()

        response: Response = self.client.get(url, {"char_id": char_obj.id})
        data = response.json()
        self.assertEqual(response.status_code, 200)

        self.assertEqual(data.get("data"), char_data)
        self.assertEqual(data.get("campaign_id"), campaign_obj.id)

    def test_get_character_incorrect_query(self):
        url = reverse("api-1.0.0:get_character_api")
        response: Response = self.client.get(url, {"id": "Hello, world!"})
        self.assertEqual(response.status_code, 400)
