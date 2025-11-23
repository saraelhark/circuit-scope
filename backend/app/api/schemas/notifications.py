"""Pydantic notification schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    actor_id: UUID | None
    project_id: UUID
    thread_id: UUID | None
    type: str
    message: str
    is_read: bool
    created_at: datetime

    project_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UnreadCountResponse(BaseModel):
    count: int
