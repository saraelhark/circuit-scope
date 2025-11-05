"""Authentication-related API routes.

Currently provides a user sync endpoint used by the frontend after
OAuth login (via Nuxt Auth / Auth.js) to ensure there is a corresponding
`User` row in the database.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.api.schemas.auth import UserResponse, UserSyncRequest
from db.models import User


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

    if payload.email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required to sync user.",
        )

    result = await session.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is None:
        # Create a new user record for this email
        user = User(
            email=payload.email,
            display_name=payload.display_name,
            avatar_url=payload.avatar_url,
        )
        session.add(user)
    else:
        # Light-touch profile sync: update basic fields when we get new values
        if payload.display_name and payload.display_name != user.display_name:
            user.display_name = payload.display_name
        if payload.avatar_url and payload.avatar_url != user.avatar_url:
            user.avatar_url = payload.avatar_url

    await session.commit()
    await session.refresh(user)

    return user
