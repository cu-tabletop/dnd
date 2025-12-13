import logging

from services.settings import settings


logger = logging.getLogger(__name__)


def ensure_bucket(name: str) -> None:
    if settings.minio.bucket_exists(name):
        return
    settings.minio.make_bucket(name)
    logger.info("Created bucket %s", name)
