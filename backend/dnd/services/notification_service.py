import json
import redis
from django.conf import settings
from typing import Dict, Any


class NotificationService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )

    def send_invitation_notification(
        self, telegram_id: int, invitation_data: Dict[str, Any]
    ):
        """Отправка уведомления о новом приглашении через Redis"""
        try:
            channel_name = f"notifications:{telegram_id}"
            self.redis_client.publish(
                channel_name,
                json.dumps(
                    {"type": "new_invitation", "data": invitation_data}
                ),
            )
        except Exception as e:
            print(f"Error sending Redis notification: {e}")

    def send_invitation_accepted_notification(
        self, master_telegram_id: int, data: Dict[str, Any]
    ):
        """Уведомление мастеру о принятии приглашения"""
        try:
            channel_name = f"notifications:{master_telegram_id}"
            self.redis_client.publish(
                channel_name,
                json.dumps({"type": "invitation_accepted", "data": data}),
            )
        except Exception as e:
            print(f"Error sending Redis notification: {e}")


notification_service = NotificationService()
