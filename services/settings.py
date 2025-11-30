from typing import Set, Any, Optional
from zoneinfo import ZoneInfo

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "dnd"
    LOG_LEVEL: str = "INFO"
    TZ: str = Field(default="Europe/Moscow")

    TOKEN_ADMIN: str = Field(alias="ADMIN_BOT_TOKEN")
    TOKEN_PLAYER: str = Field(alias="PLAYER_BOT_TOKEN")
    ADMIN_IDS: Set[int]

    # ^ PostgreSQL
    DB_HOST: str = Field(default="db", alias="POSTGRES_HOST")
    DB_PORT: int = Field(default=5432, alias="POSTGRES_PORT")
    DB_NAME: str = Field(default="db", alias="POSTGRES_DB")
    DB_USER: str = Field(default="admin", alias="POSTGRES_USER")
    DB_PASSWORD: str = Field(default="admin", alias="POSTGRES_PASSWORD")

    # ^ Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str

    # ^ Tortoise ORM
    tortoise_app: str = Field(default="models", alias="TORTOISE_APP")
    tortoise_models: tuple[str, ...] = Field(
        default=("db.models", "aerich.models"), alias="TORTOISE_MODELS"
    )
    tortoise_generate_schemas: bool = Field(
        default=False, alias="TORTOISE_GENERATE_SCHEMAS"
    )

    @computed_field
    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.pg_user}:{self.pg_password}@"
            f"{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )

    @computed_field
    @property
    def tortoise_db_url(self) -> str:
        return (
            f"postgres://{self.pg_user}:{self.pg_password}@"
            f"{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )

    @computed_field
    @property
    def tortoise_config(self) -> dict[str, Any]:
        return {
            "connections": {"default": self.tortoise_db_url},
            "apps": {
                self.tortoise_app: {
                    "models": self.tortoise_models,
                    "default_connection": "default",
                }
            },
        }

    _timezone: Optional[ZoneInfo] = None

    @computed_field
    @property
    def timezone(self) -> ZoneInfo:
        if self._timezone is None:
            self._timezone = ZoneInfo(self.TZ)
        return self._timezone

    # Конфигурация модели
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()  # type: ignore
