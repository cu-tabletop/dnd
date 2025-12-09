from aiogram import types

from db.models import User
from services.settings import settings


async def get_or_create_user(user: types.User):
    return await User.get_or_create(
        id=user.id,
        defaults={
            "id": user.id,
            "admin": user.id in settings.ADMIN_IDS,
            "username": user.username if user.username else None,
        },
    )
