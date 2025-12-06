import asyncio
import contextlib
import importlib
import inspect
import logging
import signal
from collections.abc import Generator
from contextlib import suppress
from pathlib import Path
from types import ModuleType
from typing import Any

import redis.asyncio as redis
from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from aiogram_dialog import setup_dialogs

from db.main import close_db, init_db
from services import json
from services.settings import settings

logger = logging.getLogger(__name__)

HANDLERS_PACKAGE = "handlers"
HANDLERS_PATH = Path(__file__).parent / "handlers"

MIDDLEWARE_PACKAGE = "middleware"
MIDDLEWARE_PATH = Path(__file__).parent / "middleware"


def _iter_modules(
    path: Path,
    package: str,
) -> Generator[Any, ModuleType]:
    for module in path.rglob("*.py"):
        if module.name == "__init__.py":
            continue
        relative = module.relative_to(path).with_suffix("")
        dotted = ".".join((package, *relative.parts))
        yield module.name, importlib.import_module(dotted)


def register_all_handlers(
    dp: Dispatcher,
    path: Path = HANDLERS_PATH,
    package: str = HANDLERS_PACKAGE,
) -> None:
    routers = []
    for _, module in _iter_modules(path, package):
        router = getattr(module, "router", None)
        if router is None:
            continue
        routers.append(router)

    if routers:
        dp.include_routers(*routers)
    else:
        logger.warning("Не найдено ни одного роутера для регистрации")


def register_all_middlewares(
    dp: Dispatcher,
    path: Path = MIDDLEWARE_PATH,
    package: str = MIDDLEWARE_PACKAGE,
) -> None:
    for file_name, module in _iter_modules(path, package):
        if file_name.startswith("update_"):
            target = dp.update.middleware
        elif file_name.startswith("message_"):
            target = dp.message.middleware
        elif file_name.startswith("callback_"):
            target = dp.callback_query.middleware
        else:
            continue
        middleware_cls = None

        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseMiddleware) and obj is not BaseMiddleware:
                middleware_cls = obj
                break

        if middleware_cls is None:
            logger.warning("В файле %s не найден класс middleware", file_name)
            continue

        instance = middleware_cls()
        target.register(instance)
        logger.info("Middleware %s зарегистрирован из %s", middleware_cls.__name__, file_name)


async def on_startup(bot: Bot) -> None: ...


async def on_shutdown(bot: Bot) -> None: ...


BOT_PROPERTIES = DefaultBotProperties(parse_mode=ParseMode.HTML)


async def run_bot(
    token: str,
    redis_db: int,
    suffix: str,
    properties: DefaultBotProperties = BOT_PROPERTIES,
) -> None:
    storage = RedisStorage(
        redis=redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=redis_db,
        ),
        key_builder=DefaultKeyBuilder(with_destiny=True),
        json_dumps=json.json_dumps,
        json_loads=json.json_loads,
    )

    bot = Bot(
        token=token,
        default=properties,
    )
    dp = Dispatcher(storage=storage)

    if token == settings.TOKEN_ADMIN:
        settings.admin_bot = bot
    else:
        settings.player_bot = bot

    register_all_middlewares(dp, path=MIDDLEWARE_PATH / suffix, package=MIDDLEWARE_PACKAGE + "." + suffix)
    register_all_middlewares(dp, path=MIDDLEWARE_PATH / "shared", package=MIDDLEWARE_PACKAGE + "." + "shared")
    register_all_handlers(dp, path=HANDLERS_PATH / suffix, package=HANDLERS_PACKAGE + "." + suffix)
    setup_dialogs(dp)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        await dp.start_polling(bot, handle_signals=False)
    finally:
        await dp.storage.close()
        await bot.session.close()


async def run_bot_safe(*args, **kwargs):
    with contextlib.suppress(asyncio.CancelledError):
        await run_bot(*args, **kwargs)


async def main() -> None:
    logger.info("Запущен проект: %s", settings.PROJECT_NAME)

    await init_db()
    # стартуем ботов как background задачи
    task_player = asyncio.create_task(
        run_bot_safe(
            settings.TOKEN_PLAYER,
            0,
            "player",
        ),
    )
    task_admin = asyncio.create_task(
        run_bot_safe(
            settings.TOKEN_ADMIN,
            1,
            "admin",
        ),
    )

    supress(task_admin, task_player)

    await asyncio.gather(task_player, task_admin)


def supress(*tasks):
    loop = asyncio.get_running_loop()
    with suppress(NotImplementedError):  # pragma: no cover
        # Signals handling is not supported on Windows
        # It also can't be covered on Windows
        loop.add_signal_handler(
            signal.SIGTERM,
            lambda _: cancel_tasks(*tasks),
            signal.SIGTERM,
        )
        loop.add_signal_handler(
            signal.SIGINT,
            lambda _: cancel_tasks(*tasks),
            signal.SIGINT,
        )


def cancel_tasks(*tasks):
    logger.warning("Получен ctrl+c, завершаем...")
    for task in tasks:
        task.cancel()
    asyncio.gather(close_db())


if __name__ == "__main__":
    logging.basicConfig(level=settings.LOG_LEVEL)
    asyncio.run(main())
