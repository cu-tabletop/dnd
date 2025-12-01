import asyncio
import importlib
import logging
import signal
from contextlib import suppress
from pathlib import Path
import inspect

import redis.asyncio as redis
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from aiogram_dialog import setup_dialogs

from db.main import init_db, close_db
from services import json
from services.settings import settings

logger = logging.getLogger(__name__)

HANDLERS_PACKAGE = "handlers"
HANDLERS_PATH = Path(__file__).parent / "handlers"

MIDDLEWARE_PACKAGE = "middleware"
MIDDLEWARE_PATH = Path(__file__).parent / "middleware"


def _iter_handler_modules(
    path,
    package,
):
    for module in path.rglob("*.py"):
        if module.name == "__init__.py":
            continue
        relative = module.relative_to(path).with_suffix("")
        dotted = ".".join((package, *relative.parts))
        yield module.name, importlib.import_module(dotted)


def register_all_handlers(
    dp: Dispatcher,
    path=HANDLERS_PATH,
    package=HANDLERS_PACKAGE,
) -> None:
    routers = []
    for _, module in _iter_handler_modules(path, package):
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
    path=MIDDLEWARE_PATH,
    package=MIDDLEWARE_PACKAGE,
) -> None:
    for file_name, module in _iter_handler_modules(path, package):
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
            logger.warning(f"В файле {file_name} не найден класс middleware")
            continue

        try:
            instance = middleware_cls()
            target.register(instance)
            logger.info(f"Middleware {middleware_cls.__name__} зарегистрирован из {file_name}")
        except Exception as e:
            logger.error(f"Ошибка регистрации {middleware_cls.__name__}: {e}")


async def on_startup(bot: Bot) -> None: ...


async def on_shutdown(bot: Bot) -> None: ...


async def run_bot(
    token: str,
    redis_db: int,
    suffix: str,
    properties=DefaultBotProperties(parse_mode=ParseMode.HTML),
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
    try:
        await run_bot(*args, **kwargs)
    except asyncio.CancelledError:
        pass


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
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(levelname)s:%(name)s:%(message)s",
    )
    asyncio.run(main())
