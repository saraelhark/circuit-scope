"""Application settings configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import AnyHttpUrl, Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration values loaded from environment variables."""

    app_name: str = "Circuit Scope API"
    debug: bool = False
    api_prefix: str = "/api/v1"

    database_url: str

    cors_origins: list[AnyHttpUrl] | None = Field(
        default=None, description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])

    storage_backend: str = Field(
        default="local", description="Selected storage backend identifier"
    )
    storage_local_base_path: Path = Field(default_factory=lambda: Path("./var/storage"))
    storage_public_base_url: HttpUrl | None = Field(
        default=None, description="Base URL for serving stored files"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: str | list[str] | None) -> list[str] | None:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("storage_local_base_path", mode="before")
    @classmethod
    def convert_storage_path(cls, value: str | Path) -> Path:
        if isinstance(value, Path):
            return value
        return Path(value).expanduser().resolve()

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> "Settings":
    """Return a cached settings instance."""

    return Settings()


settings: Annotated[Settings, Field()] = get_settings()

__all__ = ["settings", "get_settings", "Settings"]
