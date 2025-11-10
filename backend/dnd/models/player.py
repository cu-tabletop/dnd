from django.db import models


class Player(models.Model):
    id = models.AutoField(primary_key=True, auto_created=True)
    telegram_id = models.BigIntegerField()
    admin = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
