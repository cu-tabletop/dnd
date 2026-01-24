from tortoise import fields

from utils.enums import Role

from .base import TimestampedModel, UuidModel


class Participation(TimestampedModel, UuidModel):
    user = fields.ForeignKeyField("models.User")
    campaign = fields.ForeignKeyField("models.Campaign")
    role = fields.IntEnumField(Role)

    class Meta:
        unique_together = ("user", "campaign")
