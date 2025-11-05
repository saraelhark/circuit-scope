"""Pydantic schemas for authentication and user synchronization."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserSyncRequest(BaseModel):
    """Payload used by the frontend to sync OAuth-authenticated users with the DB."""

    email: EmailStr = Field(...)
    display_name: str | None = Field(default=None, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=500)


class UserResponse(BaseModel):
    """Representation of a user returned to the frontend."""

    id: UUID
    email: EmailStr | None
    display_name: str | None
    avatar_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


__all__ = ["UserSyncRequest", "UserResponse"]
