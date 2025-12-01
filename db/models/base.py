import uuid

from tortoise import fields, models


class UuidModel(models.Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)

    class Meta:
        abstract = True


class TimestampedModel(models.Model):
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True


class CharacterData(models.Model):
    data = fields.JSONField(null=True)

    class Meta:
        abstract = True
