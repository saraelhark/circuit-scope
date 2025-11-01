"""Routes for comment threads and comments."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.api.schemas.comment_threads import (
    CommentThreadCreate,
    CommentThreadListResponse,
    CommentThreadResponse,
    ThreadCommentCreate,
    ThreadCommentResponse,
    ThreadResolutionUpdate,
)
from app.services.comment_threads import (
    add_comment,
    create_thread,
    delete_comment,
    delete_thread,
    list_threads,
    update_thread_resolution,
)

router = APIRouter(prefix="/projects/{project_id}/threads", tags=["comment-threads"])


@router.get("/", response_model=CommentThreadListResponse)
async def list_comment_threads(
    project_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> CommentThreadListResponse:
    return await list_threads(session, project_id=project_id)


@router.post("/", response_model=CommentThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_comment_thread(
    project_id: UUID,
    payload: CommentThreadCreate,
    session: AsyncSession = Depends(get_db_session),
) -> CommentThreadResponse:
    return await create_thread(session, project_id=project_id, payload=payload)


@router.post(
    "/{thread_id}/comments",
    response_model=ThreadCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment_thread_reply(
    project_id: UUID,
    thread_id: UUID,
    payload: ThreadCommentCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ThreadCommentResponse:
    return await add_comment(
        session,
        project_id=project_id,
        thread_id=thread_id,
        payload=payload,
    )


@router.patch(
    "/{thread_id}/resolution",
    response_model=CommentThreadResponse,
)
async def update_comment_thread_resolution(
    project_id: UUID,
    thread_id: UUID,
    payload: ThreadResolutionUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> CommentThreadResponse:
    return await update_thread_resolution(
        session,
        project_id=project_id,
        thread_id=thread_id,
        payload=payload,
    )


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment_thread(
    project_id: UUID,
    thread_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await delete_thread(session, project_id=project_id, thread_id=thread_id)
    return None


@router.delete(
    "/{thread_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_comment_thread_comment(
    project_id: UUID,
    thread_id: UUID,
    comment_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await delete_comment(
        session,
        project_id=project_id,
        thread_id=thread_id,
        comment_id=comment_id,
    )
    return None
