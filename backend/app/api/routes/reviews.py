"""Routes for project reviews/comments."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db_session
from app.api.schemas.reviews import (
    ReviewCreate,
    ReviewListResponse,
    ReviewResponse,
)
from app.services.reviews import (
    create_review,
    list_reviews,
)
from db.models import User

router = APIRouter()


@router.get("/", response_model=ReviewListResponse)
async def list_project_reviews(
    project_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ReviewListResponse:
    """List all reviews for a project."""
    return await list_reviews(session, project_id)


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_project_review(
    project_id: UUID,
    payload: ReviewCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ReviewResponse:
    """Create a review for a project. Requires authentication."""
    return await create_review(session, project_id, payload, current_user.id)
