import asyncio
import importlib
import logging
from pathlib import Path
from types import ModuleType
from typing import Iterable

import redis.asyncio as redis
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from aiogram_dialog import setup_dialogs

from settings import settings

logger = logging.getLogger(__name__)

HANDLERS_PACKAGE = "handlers"
HANDLERS_PATH = Path(__file__).parent / "handlers"

DIALOGS_PACKAGE = "dialogs"
DIALOGS_PATH = Path(__file__).parent / "dialogs"


def register_all_middlewares(dp: Dispatcher) -> None: ...


def _iter_handler_modules() -> Iterable[ModuleType]:
    for path, package in (
        (HANDLERS_PATH, HANDLERS_PACKAGE),
        (DIALOGS_PATH, DIALOGS_PACKAGE),
    ):
        for module in path.rglob("*.py"):
            if module.name == "__init__.py":
                continue
            relative = module.relative_to(path).with_suffix("")
            dotted = ".".join((package, *relative.parts))
            logger.info(f"included {dotted}")
            import_module = importlib.import_module(dotted)
            yield import_module


def register_all_handlers(dp: Dispatcher) -> None:
    routers = []
    for module in _iter_handler_modules():
        router = getattr(module, "router", None)
        if router is None:
            continue
        logger.info(f"\tadded: {router}")
        routers.append(router)

    if routers:
        dp.include_routers(*routers)
    else:
        logger.warning("Не найдено ни одного роутера для регистрации")


async def on_startup(bot: Bot) -> None: ...


async def on_shutdown(bot: Bot) -> None: ...


async def run_bot() -> None:
    storage = RedisStorage(
        redis=redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
        ),
        key_builder=DefaultKeyBuilder(with_destiny=True),
    )

    bot = Bot(
        token=settings.TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher(storage=storage)

    register_all_middlewares(dp)
    register_all_handlers(dp)
    setup_dialogs(dp)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        await dp.start_polling(bot)
    finally:
        await dp.storage.close()
        await bot.session.close()


async def main() -> None:
    logger.info("Запущен бот в проекте: %s", settings.PROJECT_NAME)

    await run_bot()


if __name__ == "__main__":
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(levelname)s:%(name)s:%(message)s",
    )
    asyncio.run(main())
