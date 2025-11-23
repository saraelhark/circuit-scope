"""Service layer for comment threads and comments."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas.comment_threads import (
    CommentThreadCreate,
    CommentThreadListResponse,
    CommentThreadResponse,
    ThreadAnnotation,
    ThreadCommentCreate,
    ThreadCommentResponse,
    ThreadResolutionUpdate,
)
from app.services.projects import ensure_project_exists
from app.services.notifications import create_notification
from db.models import CommentThread, ThreadComment, Project


async def list_threads(
    session: AsyncSession,
    *,
    project_id: UUID,
) -> CommentThreadListResponse:
    """List threads for a project."""
    await ensure_project_exists(session, project_id)

    query: Select[tuple[CommentThread]] = (
        select(CommentThread)
        .where(CommentThread.project_id == project_id)
        .options(
            selectinload(CommentThread.comments).selectinload(ThreadComment.author)
        )
        .order_by(CommentThread.created_at.asc())
    )

    result = await session.execute(query)
    threads: Sequence[CommentThread] = result.scalars().unique().all()

    total_count = len(threads)
    resolved_count = sum(1 for thread in threads if thread.is_resolved)
    open_count = total_count - resolved_count

    return CommentThreadListResponse(
        project_id=project_id,
        items=[_serialize_thread(thread) for thread in threads],
        total_count=total_count,
        open_count=open_count,
        resolved_count=resolved_count,
    )


async def create_thread(
    session: AsyncSession,
    *,
    project_id: UUID,
    payload: CommentThreadCreate,
) -> CommentThreadResponse:
    """Create a new thread."""
    await ensure_project_exists(session, project_id)

    created_by_id = payload.created_by_id or payload.initial_comment.author_id

    thread = CommentThread(
        project_id=project_id,
        view_id=payload.view_id,
        pin_x=payload.pin_x,
        pin_y=payload.pin_y,
        annotation=payload.annotation.model_dump() if payload.annotation else None,
        created_by_id=created_by_id,
    )

    initial = payload.initial_comment
    initial_comment = ThreadComment(
        content=initial.content,
        author_id=initial.author_id,
        guest_name=initial.guest_name,
        guest_email=str(initial.guest_email) if initial.guest_email else None,
    )
    thread.comments.append(initial_comment)

    session.add(thread)
    await session.commit()

    result = await session.execute(
        select(CommentThread)
        .options(
            selectinload(CommentThread.comments).selectinload(ThreadComment.author)
        )
        .where(CommentThread.id == thread.id)
    )
    thread_with_comments = result.scalar_one()

    project = await session.get(Project, project_id)
    if project and project.owner_id != created_by_id:
        await create_notification(
            session,
            user_id=project.owner_id,
            actor_id=created_by_id,
            project_id=project_id,
            thread_id=thread.id,
            type="comment_thread_created",
            message=f"New comment thread on {project.name}",
        )

    return _serialize_thread(thread_with_comments)


async def add_comment(
    session: AsyncSession,
    *,
    project_id: UUID,
    thread_id: UUID,
    payload: ThreadCommentCreate,
) -> ThreadCommentResponse:
    """Add a new comment to a thread."""
    thread = await _get_thread(session, project_id, thread_id)

    if payload.parent_id is not None:
        parent = await session.get(ThreadComment, payload.parent_id)
        if parent is None or parent.thread_id != thread.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid parent comment"
            )

    comment = ThreadComment(
        thread_id=thread.id,
        content=payload.content,
        parent_id=payload.parent_id,
        author_id=payload.author_id,
        guest_name=payload.guest_name,
        guest_email=str(payload.guest_email) if payload.guest_email else None,
    )

    session.add(comment)
    await session.commit()

    query = (
        select(ThreadComment)
        .options(selectinload(ThreadComment.author))
        .where(ThreadComment.id == comment.id)
    )
    result = await session.execute(query)
    comment = result.scalar_one()

    project = await session.get(Project, project_id)
    if project:
        if project.owner_id != payload.author_id:
            await create_notification(
                session,
                user_id=project.owner_id,
                actor_id=payload.author_id,
                project_id=project_id,
                thread_id=thread.id,
                type="comment_reply",
                message=f"New reply on {project.name}",
            )

        if (
            thread.created_by_id
            and thread.created_by_id != payload.author_id
            and thread.created_by_id != project.owner_id
        ):
            await create_notification(
                session,
                user_id=thread.created_by_id,
                actor_id=payload.author_id,
                project_id=project_id,
                thread_id=thread.id,
                type="comment_reply",
                message=f"New reply on your thread in {project.name}",
            )

    return ThreadCommentResponse.model_validate(comment, from_attributes=True)


async def update_thread_resolution(
    session: AsyncSession,
    *,
    project_id: UUID,
    thread_id: UUID,
    payload: ThreadResolutionUpdate,
) -> CommentThreadResponse:
    """Update the resolution status of a thread."""
    thread = await _get_thread(session, project_id, thread_id)

    if payload.is_resolved:
        thread.is_resolved = True
        thread.resolved_by_id = payload.resolved_by_id
        thread.resolved_at = datetime.now(timezone.utc)
    else:
        thread.is_resolved = False
        thread.resolved_by_id = None
        thread.resolved_at = None

    await session.commit()
    await session.refresh(thread)

    if (
        payload.is_resolved
        and thread.created_by_id
        and thread.created_by_id != payload.resolved_by_id
    ):
        project = await session.get(Project, project_id)
        if project:
            await create_notification(
                session,
                user_id=thread.created_by_id,
                actor_id=payload.resolved_by_id,
                project_id=project_id,
                thread_id=thread.id,
                type="thread_resolved",
                message=f"Your thread on {project.name} was marked as resolved",
            )

    return _serialize_thread(thread)


async def delete_thread(
    session: AsyncSession,
    *,
    project_id: UUID,
    thread_id: UUID,
) -> None:
    """Delete a thread."""
    thread = await _get_thread(session, project_id, thread_id)
    await session.delete(thread)
    await session.commit()


async def delete_comment(
    session: AsyncSession,
    *,
    project_id: UUID,
    thread_id: UUID,
    comment_id: UUID,
) -> None:
    """Delete a comment."""
    thread = await _get_thread(session, project_id, thread_id)

    comment = await session.get(ThreadComment, comment_id)
    if comment is None or comment.thread_id != thread.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    await session.delete(comment)
    await session.commit()


async def _get_thread(
    session: AsyncSession,
    project_id: UUID,
    thread_id: UUID,
) -> CommentThread:
    query = (
        select(CommentThread)
        .options(
            selectinload(CommentThread.comments).selectinload(ThreadComment.author)
        )
        .where(CommentThread.project_id == project_id, CommentThread.id == thread_id)
    )
    result = await session.execute(query)
    thread = result.scalar_one_or_none()
    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found"
        )
    return thread


def _serialize_thread(thread: CommentThread) -> CommentThreadResponse:
    comment_models = [
        ThreadCommentResponse.model_validate(c, from_attributes=True)
        for c in thread.comments
    ]

    annotation: ThreadAnnotation | None = None
    if thread.annotation:
        annotation = ThreadAnnotation.model_validate(thread.annotation)

    return CommentThreadResponse(
        id=thread.id,
        project_id=thread.project_id,
        view_id=thread.view_id,
        pin_x=thread.pin_x,
        pin_y=thread.pin_y,
        annotation=annotation,
        is_resolved=thread.is_resolved,
        created_by_id=thread.created_by_id,
        resolved_by_id=thread.resolved_by_id,
        resolved_at=thread.resolved_at,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        comments=comment_models,
        comment_count=len(comment_models),
    )


__all__ = [
    "add_comment",
    "create_thread",
    "delete_comment",
    "delete_thread",
    "list_threads",
    "update_thread_resolution",
]
