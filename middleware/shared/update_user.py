import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware, types
from aiogram.types import TelegramObject, Message, CallbackQuery, Update

from db.models import User


logger = logging.getLogger(__name__)


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) or isinstance(event, CallbackQuery):
            user, created = await self._get_user(event.from_user)
            if created:
                logger.info("New user created with id: %d and username %s", user.id, user.username)
            return await handler(event, {**data, "user": user})
        if isinstance(event, Update):
            tg_user = (
                (event.message and event.message.from_user)
                or (event.callback_query and event.callback_query.from_user)
                or (event.my_chat_member and event.my_chat_member.from_user)
                or (event.chat_join_request and event.chat_join_request.from_user)
            )

            if tg_user:
                user, created = await self._get_user(tg_user)
                if created:
                    logger.info("New user created with id: %d and username %s", user.id, user.username)
                return await handler(event, {**data, "user": user})
        return await handler(event, data)

    @staticmethod
    async def _get_user(user: types.User):
        return await User.get_or_create(
            id=user.id,
            defaults={
                "id": user.id,
                "username": user.username if user.username else None,
            },
        )
