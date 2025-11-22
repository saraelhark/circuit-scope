"""Authentication-related API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.api.schemas.auth import UserResponse, UserSyncRequest
from app.services.users import sync_user


router = APIRouter()


@router.post("/sync", response_model=UserResponse)
async def sync_authenticated_user(
    payload: UserSyncRequest,
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Create or update a `User` based on OAuth session data.

    The frontend should call this after a successful OAuth login, passing the
    user's email and optional profile information (display name, avatar URL).
    """

    try:
        return await sync_user(session, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
