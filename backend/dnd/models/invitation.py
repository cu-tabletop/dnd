from django.db import models
from django.utils import timezone
from datetime import timedelta
import secrets


class Invitation(models.Model):
    STATUS_CHOICES = (
        ("pending", "Ожидает ответа"),
        ("accepted", "Принято"),
        ("postponed", "Отложено"),
        ("expired", "Просрочено"),
    )

    campaign = models.ForeignKey("Campaign", on_delete=models.CASCADE)
    invited_player = models.ForeignKey(
        "Player", on_delete=models.CASCADE, related_name="received_invitations"
    )
    invited_by = models.ForeignKey(
        "Player", on_delete=models.CASCADE, related_name="sent_invitations"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    token = models.CharField(max_length=100, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invitations"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at
