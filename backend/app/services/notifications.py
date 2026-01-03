"""Notification service."""

from __future__ import annotations

from uuid import UUID
from typing import Sequence

from sqlalchemy import func, select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Notification


async def get_notifications(
    session: AsyncSession, user_id: UUID, page: int = 1, size: int = 20
) -> tuple[Sequence[Notification], int]:
    """Get notifications for a user."""
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .options(selectinload(Notification.project))
        .order_by(desc(Notification.created_at))
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await session.execute(stmt)
    notifications = result.scalars().all()

    count_stmt = (
        select(func.count())  # pylint: disable=not-callable
        .select_from(Notification)
        .where(Notification.user_id == user_id)
    )
    count_result = await session.execute(count_stmt)
    total = count_result.scalar_one()

    # Enrich with project name
    for notification in notifications:
        if notification.project:
            notification.project_name = notification.project.name

    return notifications, total


async def get_unread_count(session: AsyncSession, user_id: UUID) -> int:
    """Get unread notification count for a user."""
    stmt = (
        select(func.count())  # pylint: disable=not-callable
        .select_from(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def mark_as_read(
    session: AsyncSession, notification_id: UUID, user_id: UUID
) -> Notification | None:
    """Mark a notification as read."""
    stmt = (
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user_id)
        .values(is_read=True)
        .returning(Notification)
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.scalar_one_or_none()


async def mark_all_as_read(session: AsyncSession, user_id: UUID) -> None:
    """Mark all notifications as read for a user."""
    stmt = (
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    await session.execute(stmt)
    await session.commit()


async def create_notification(
    session: AsyncSession,
    user_id: UUID,
    actor_id: UUID | None,
    project_id: UUID,
    thread_id: UUID | None,
    type: str,
    message: str,
) -> Notification:
    """Create a new notification."""
    notification = Notification(
        user_id=user_id,
        actor_id=actor_id,
        project_id=project_id,
        thread_id=thread_id,
        type=type,
        message=message,
    )
    session.add(notification)
    await session.commit()
    await session.refresh(notification)
    return notification
