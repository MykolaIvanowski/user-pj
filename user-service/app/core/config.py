from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    DB_URL: SecretStr = Field(description="SQLAlchemy database URL, e.g. postgresql+asyncpg://user:pass@host/db")
    JWT_SECRET: SecretStr = Field(min_length=32, description="HS256 secret, at least 32 chars")
    JWT_EXPIRE: int = Field(default=3600, ge=60, le=86400 * 30, description="JWT expiry in seconds")
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    ENV: str = Field(default="production", pattern="^(development|testing|production)$")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


# Backwards-compat for `from app.core.config import settings`
settings = get_settings()
