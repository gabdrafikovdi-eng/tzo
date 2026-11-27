from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class DataBaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    POSTGRES_USER: str = Field(description="Пользователь PostgreSQL")
    POSTGRES_PASSWORD: str = Field(description="Пароль PostgreSQL")
    POSTGRES_HOST: str = Field(description="Хост PostgreSQL")
    POSTGRES_PORT: str = Field(description="Порт PostgreSQL")
    POSTGRES_DB: str = Field(description="Имя БД")

    @property
    def DATABASE_URL(self) -> str:
        # Формат: postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DB
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


data_base_conf = DataBaseConfig()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    COOKIE_SECURE: bool = True
    HTTPONLY: bool = True
    NBYTES_SECRET_USER_SESSION: int = 32
    TELEGRAM_BOT: str = Field(
        validation_alias=AliasChoices("TELEGRAM_BOT", "TELEGRAM_TOKEN")
    )
    TELEGRAM_INIT_DATA_EXPIRES: int = Field(
        default=900,
        description="Как долго данные инициализации остаются пригодными для использования (в секундах). Рекомендуется 300–900 для Telegram Mini App",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
