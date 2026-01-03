"""Routes for comment threads and comments."""

from uuid import UUID

from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.core.rate_limit import limiter
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

router = APIRouter()


@router.get("/", response_model=CommentThreadListResponse)
async def list_comment_threads(
    project_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> CommentThreadListResponse:
    """List all review threads for a project."""
    return await list_threads(session, project_id=project_id)


@router.post("/", response_model=CommentThreadResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_comment_thread(
    request: Request,
    project_id: UUID,
    payload: CommentThreadCreate,
    session: AsyncSession = Depends(get_db_session),
) -> CommentThreadResponse:
    """Create a new review thread."""
    return await create_thread(session, project_id=project_id, payload=payload)


@router.post(
    "/{thread_id}/comments",
    response_model=ThreadCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
async def create_comment_thread_reply(
    request: Request,
    project_id: UUID,
    thread_id: UUID,
    payload: ThreadCommentCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ThreadCommentResponse:
    """Add a new comment to a review thread."""
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
    """Update the resolution of a review thread."""
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
    """Delete a review thread."""
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
    """Delete a comment from a review thread."""
    await delete_comment(
        session,
        project_id=project_id,
        thread_id=thread_id,
        comment_id=comment_id,
    )
    return None
