import logging

from exceptions.minio import BucketsUncreatedError
from services.settings import settings
from utils.minio import ensure_bucket

logger = logging.getLogger(__name__)


async def init_minio() -> None:
    for bucket_name in settings.MINIO_BUCKETS:
        ensure_bucket(bucket_name)
    logger.info("Minio инициализирована")


async def test_minio() -> None:
    """Проверка подключения к Minio"""

    created_buckets = {b.name for b in settings.minio.list_buckets()}
    logger.debug("Minio created buckets %s", created_buckets)
    for bucket in settings.MINIO_BUCKETS:
        if bucket not in created_buckets:
            raise BucketsUncreatedError(bucket)
    logger.info("Соединение с Minio успешно")
