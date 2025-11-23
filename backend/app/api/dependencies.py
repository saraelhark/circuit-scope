"""Common API dependencies."""

from __future__ import annotations

from uuid import UUID
from fastapi import Depends, Request, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.storage.base import StorageService
from db.sessions import get_session
from db.models import User


async def get_db_session(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    """Provide database session dependency for FastAPI routes."""

    return session


async def get_current_user(
    x_user_id: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Get the current user from the X-User-Id header."""
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID header missing"
        )

    try:
        user_uuid = UUID(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid User ID format"
        )

    user = await session.get(User, user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


def get_storage_service(request: Request) -> StorageService:
    """Retrieve the storage service from the application state."""

    storage: StorageService | None = getattr(request.app.state, "storage_service", None)
    if storage is None:
        raise RuntimeError("Storage service is not configured")
    return storage
