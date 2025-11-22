"""Storage service factory functions."""

from __future__ import annotations

from typing import Final

from app.core.config import Settings
from app.services.storage.base import StorageService
from app.services.storage.local import LocalStorage
from app.services.storage.s3 import S3Storage


SUPPORTED_BACKENDS: Final[set[str]] = {"local", "s3"}


def create_storage_service(settings: Settings) -> StorageService:
    """Create a storage service instance based on configuration."""

    backend = settings.storage_backend.lower()

    if backend == "local":
        return LocalStorage(
            base_path=settings.storage_local_base_path,
            public_base_url=(
                str(settings.storage_public_base_url)
                if settings.storage_public_base_url
                else None
            ),
        )

    if backend == "s3":
        if not settings.storage_s3_bucket:
            raise ValueError("S3 bucket name is required for S3 backend")

        return S3Storage(
            bucket_name=settings.storage_s3_bucket,
            region_name=settings.storage_s3_region,
            access_key=settings.storage_s3_access_key,
            secret_key=settings.storage_s3_secret_key,
            endpoint_url=settings.storage_s3_endpoint,
            public_base_url=(
                str(settings.storage_public_base_url)
                if settings.storage_public_base_url
                else None
            ),
        )

    raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")
