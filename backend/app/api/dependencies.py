"""Common API dependencies."""

from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.storage.base import StorageService
from db.sessions import get_session


async def get_db_session(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    """Provide database session dependency for FastAPI routes."""

    return session


def get_storage_service(request: Request) -> StorageService:
    """Retrieve the storage service from the application state."""

    storage: StorageService | None = getattr(request.app.state, "storage_service", None)
    if storage is None:
        raise RuntimeError("Storage service is not configured")
    return storage
