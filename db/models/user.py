from tortoise import fields, models

from .base import TimestampedModel, CharacterData


class User(TimestampedModel, CharacterData):
    id = fields.BigIntField(pk=True)
    username = fields.CharField(max_length=32, null=True, index=True)
    admin = fields.BooleanField(index=True, default=False)

    class Meta:
        unique_together = ("id", "username")
