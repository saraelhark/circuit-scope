"""Routes for project reviews/comments."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.api.schemas.reviews import (
    ReviewCreate,
    ReviewListResponse,
    ReviewResponse,
    ReviewUpdate,
)
from app.services.reviews import (
    create_review,
    delete_review,
    list_reviews,
    update_review,
)

router = APIRouter()


@router.get("/", response_model=ReviewListResponse)
async def list_project_reviews(
    project_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ReviewListResponse:
    return await list_reviews(session, project_id)


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_project_review(
    project_id: UUID,
    payload: ReviewCreate,
    x_reviewer_id: UUID | None = Header(
        default=None, description="Temporary reviewer identifier"
    ),
    session: AsyncSession = Depends(get_db_session),
) -> ReviewResponse:
    reviewer_id = payload.reviewer_id
    if reviewer_id is None:
        if x_reviewer_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reviewer ID must be provided until OAuth is implemented.",
            )
        reviewer_id = x_reviewer_id

    payload.reviewer_id = reviewer_id
    return await create_review(session, project_id, payload)


@router.patch("/{review_id}", response_model=ReviewResponse)
async def update_project_review(
    project_id: UUID,
    review_id: UUID,
    payload: ReviewUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ReviewResponse:
    return await update_review(session, project_id, review_id, payload)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_review(
    project_id: UUID,
    review_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await delete_review(session, project_id, review_id)
    return None
