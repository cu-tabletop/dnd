import logging

from tortoise import Tortoise

from services.settings import settings

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Инициализация подключения к Tortoise ORM"""

    await Tortoise.init(config=settings.tortoise_config)
    if settings.TORTOISE_GENERATE_SCHEMAS:
        await Tortoise.generate_schemas()
        logger.info("Генерация схем Tortoise ORM выполнена")
    logger.info("Tortoise ORM инициализирована")


async def close_db() -> None:
    """Закрываем все соединения с базой данных для Tortoise ORM"""

    await Tortoise.close_connections()
    logger.info("Tortoise ORM соединения закрыты")
