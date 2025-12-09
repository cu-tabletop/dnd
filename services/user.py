from aiogram import types

from db.models import User


async def get_or_create_user(user: types.User):
    return await User.get_or_create(
        id=user.id,
        defaults={
            "id": user.id,
            "username": user.username if user.username else None,
        },
    )
