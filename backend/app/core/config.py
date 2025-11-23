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

    cors_origins: list[AnyHttpUrl] = Field(description="Allowed CORS origins")
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

    storage_s3_bucket: str | None = None
    storage_s3_region: str | None = None
    storage_s3_access_key: str | None = None
    storage_s3_secret_key: str | None = None
    storage_s3_endpoint: str | None = None

    frontend_secret_key: str = Field(
        title="Frontend secret key",
        description="Secret key for frontend-to-backend authentication",
        required=True,
    )

    kicad_cli_path: str = Field(
        default="kicad-cli",
        description="Executable used for KiCad command-line operations",
    )
    kicad_cli_timeout_seconds: int = Field(
        default=120,
        description="Max seconds to wait for KiCad CLI operations before aborting",
        ge=1,
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: str | list[str]) -> list[str]:
        """Split a comma-separated string of origins into a list."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("storage_local_base_path", mode="before")
    @classmethod
    def convert_storage_path(cls, value: str | Path) -> Path:
        """Convert a string path to a Path object."""
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
