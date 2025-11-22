"""Service layer for user management."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.auth import UserSyncRequest
from db.models import User


async def sync_user(session: AsyncSession, payload: UserSyncRequest) -> User:
    """Create or update a User based on external auth data."""
    if not payload.email:
        raise ValueError("Email is required")

    result = await session.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=payload.email,
            display_name=payload.display_name,
            avatar_url=payload.avatar_url,
        )
        session.add(user)
    else:
        if payload.display_name and not user.display_name:
            user.display_name = payload.display_name
        if payload.avatar_url and not user.avatar_url:
            user.avatar_url = payload.avatar_url

    await session.commit()
    await session.refresh(user)
    return user
