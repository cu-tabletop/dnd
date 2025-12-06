from typing import Any
from zoneinfo import ZoneInfo

from aiogram import Bot
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "dnd"
    LOG_LEVEL: str = "INFO"
    TZ: str = "Europe/Moscow"

    TOKEN_ADMIN: str = ""
    TOKEN_PLAYER: str = ""
    ADMIN_IDS: set[int] = set()

    # ^ PostgreSQL
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_NAME: str = "db"
    DB_USER: str = Field(default="admin", alias="POSTGRES_USER")
    DB_PASSWORD: str = Field(default="admin", alias="POSTGRES_PASSWORD")

    # ^ Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = Field(default="secure_password")

    # ^ Tortoise ORM
    TORTOISE_APP: str = "models"
    TORTOISE_MODELS: tuple[str, ...] = ("db.models", "aerich.models")
    TORTOISE_GENERATE_SCHEMAS: bool = False

    @computed_field
    @property
    def postgres_dsn(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @computed_field
    @property
    def tortoise_db_url(self) -> str:
        return f"postgres://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @computed_field
    @property
    def tortoise_config(self) -> dict[str, Any]:
        return {
            "connections": {"default": self.tortoise_db_url},
            "apps": {
                self.TORTOISE_APP: {
                    "models": self.TORTOISE_MODELS,
                    "default_connection": "default",
                }
            },
        }

    _timezone: ZoneInfo | None = None

    @computed_field
    @property
    def timezone(self) -> ZoneInfo:
        if self._timezone is None:
            self._timezone = ZoneInfo(self.TZ)
        return self._timezone

    # Конфигурация модели
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    admin_bot: Bot | None = None
    player_bot: Bot | None = None


settings = Settings()
