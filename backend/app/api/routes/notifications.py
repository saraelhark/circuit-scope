"""Notification routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User
from app.api.dependencies import get_db_session, get_current_user
from app.api.schemas.notifications import NotificationResponse, UnreadCountResponse
from app.services.notifications import (
    get_notifications,
    get_unread_count,
    mark_all_as_read,
    mark_as_read,
)

router = APIRouter()


@router.get("/", response_model=list[NotificationResponse])
async def list_notifications(
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List notifications for the current user."""
    notifications, _ = await get_notifications(session, current_user.id, page, size)
    return notifications


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_notification_count(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get the number of unread notifications."""
    count = await get_unread_count(session, current_user.id)
    return UnreadCountResponse(count=count)


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Mark a notification as read."""
    notification = await mark_as_read(session, notification_id, current_user.id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )
    return notification


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Mark all notifications as read."""
    await mark_all_as_read(session, current_user.id)
    return None
