from tortoise import fields

from db.models.base import TimestampedModel, UuidModel
from services.role import Role


class Invite(TimestampedModel, UuidModel):
    user = fields.ForeignKeyField("models.User")
    campaign = fields.ForeignKeyField("models.Campaign")
    role = fields.IntEnumField(Role, description="На какую роль мы приглашаем пользователя")
    start_data = fields.UUIDField(index=True)
