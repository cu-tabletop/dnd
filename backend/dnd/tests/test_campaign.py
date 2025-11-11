import base64
from io import BytesIO

from PIL import Image
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient

from dnd.models import Player, Campaign, CampaignMembership


def generate_base64_icon():
    """Helper to create a small base64 PNG image."""
    image = Image.new("RGB", (10, 10), color="blue")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


class TestCampaignCreate(APITestCase):
    client: APIClient

    def setUp(self):
        self.url = reverse("api-1.0.0:create_campaign_api")
        self.player = Player.objects.create(telegram_id=111, verified=True)

    def test_campaign_create_success(self):
        data = {
            "telegram_id": self.player.telegram_id,
            "title": "Cool Campaign",
            "description": "An awesome campaign",
            "icon": generate_base64_icon(),
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Campaign.objects.count(), 1)
        self.assertEqual(CampaignMembership.objects.count(), 1)
        self.assertEqual(response.json()["message"], "created")

    def test_campaign_create_invalid_user(self):
        data = {
            "telegram_id": 9999,  # Nonexistent user
            "title": "Invalid Campaign",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 404)


class TestGetCampaignInfo(APITestCase):
    client: APIClient

    def setUp(self):
        self.url = reverse("api-1.0.0:get_campaign_info_api")
        self.owner = Player.objects.create(telegram_id=222)
        self.campaign_public = Campaign.objects.create(
            title="Public Campaign", private=False
        )
        self.campaign_private = Campaign.objects.create(
            title="Private Campaign", private=True
        )
        CampaignMembership.objects.create(
            user=self.owner, campaign=self.campaign_private, status=2
        )

    def test_get_single_public_campaign(self):
        response = self.client.get(
            self.url, {"campaign_id": self.campaign_public.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], self.campaign_public.title)

    def test_get_private_campaign_as_member(self):
        response = self.client.get(
            self.url,
            {
                "campaign_id": self.campaign_private.id,
                "user_id": self.owner.id,
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_get_private_campaign_as_non_member(self):
        response = self.client.get(
            self.url, {"campaign_id": self.campaign_private.id}
        )
        self.assertEqual(response.status_code, 404)

    def test_get_all_campaigns_for_user(self):
        new_campaign = Campaign.objects.create(
            title="Another Campaign", private=False
        )
        CampaignMembership.objects.create(
            user=self.owner, campaign=new_campaign
        )
        response = self.client.get(
            self.url, {"user_id": self.owner.telegram_id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.json(), list))
        self.assertGreaterEqual(len(response.json()), 2)


class TestAddToCampaign(APITestCase):
    client: APIClient

    def setUp(self):
        self.url = reverse("api-1.0.0:add_to_campaign_api")
        self.owner = Player.objects.create(telegram_id=333)
        self.new_user = Player.objects.create(telegram_id=334)
        self.campaign = Campaign.objects.create(title="Owner Campaign")
        CampaignMembership.objects.create(
            user=self.owner, campaign=self.campaign, status=2
        )

    def test_add_user_success(self):
        data = {
            "campaign_id": self.campaign.id,
            "owner_id": self.owner.id,
            "user_id": self.new_user.id,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            CampaignMembership.objects.filter(
                campaign=self.campaign, user=self.new_user
            ).exists()
        )

    def test_add_user_already_exists(self):
        CampaignMembership.objects.create(
            user=self.new_user, campaign=self.campaign
        )
        data = {
            "campaign_id": self.campaign.id,
            "owner_id": self.owner.id,
            "user_id": self.new_user.id,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 200)

    def test_add_user_forbidden(self):
        fake_owner = Player.objects.create(telegram_id=999)
        data = {
            "campaign_id": self.campaign.id,
            "owner_id": fake_owner.id,
            "user_id": self.new_user.id,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 403)


class TestEditPermissions(APITestCase):
    client: APIClient

    def setUp(self):
        self.url = reverse("api-1.0.0:edit_permissions_api")
        self.owner = Player.objects.create(telegram_id=444)
        self.member = Player.objects.create(telegram_id=445)
        self.campaign = Campaign.objects.create(title="Permission Campaign")
        CampaignMembership.objects.create(
            user=self.owner, campaign=self.campaign, status=2
        )
        CampaignMembership.objects.create(
            user=self.member, campaign=self.campaign, status=0
        )

    def test_edit_permission_success(self):
        data = {
            "campaign_id": self.campaign.id,
            "owner_id": self.owner.id,
            "user_id": self.member.id,
            "status": 1,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 200)

    def test_edit_permission_invalid_status(self):
        data = {
            "campaign_id": self.campaign.id,
            "owner_id": self.owner.id,
            "user_id": self.member.id,
            "status": 5,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_edit_permission_forbidden(self):
        not_owner = Player.objects.create(telegram_id=446)
        data = {
            "campaign_id": self.campaign.id,
            "owner_id": not_owner.id,
            "user_id": self.member.id,
            "status": 1,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 403)

    def test_edit_permission_user_not_found(self):
        data = {
            "campaign_id": self.campaign.id,
            "owner_id": self.owner.id,
            "user_id": 9999,
            "status": 1,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 404)
