"""Storage service factory functions."""

from __future__ import annotations

from typing import Final

from app.core.config import Settings
from app.services.storage.base import StorageService
from app.services.storage.local import LocalStorage


SUPPORTED_BACKENDS: Final[set[str]] = {"local"}


def create_storage_service(settings: Settings) -> StorageService:
    """Create a storage service instance based on configuration."""

    backend = settings.storage_backend.lower()

    if backend == "local":
        return LocalStorage(
            base_path=settings.storage_local_base_path,
        )

    raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")
