from typing import Set

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "dndadminbot"
    LOG_LEVEL: str = "INFO"

    TOKEN: str = Field(alias="ADMIN_BOT_TOKEN")
    ADMIN_IDS: Set[int]

    BACKEND_URL: str = "http://backend:8000"
    PATH_TO_DEFAULT_ICON: str = "assets/default_icon.jpg"

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str
    REDIS_DB: int = Field(alias="ADMIN_REDIS_DB")

    USE_API_STUBS: bool = False
    STUB_DELAY: float = 0.5  # Задержка для имитации сетевого запроса

    # Конфигурация модели - ИСПРАВЛЕННАЯ ВЕРСИЯ
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()  # type: ignore
