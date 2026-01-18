"""Service layer for project reviews and comments."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.reviews import (
    ReviewCreate,
    ReviewListResponse,
    ReviewResponse,
)
from app.services.projects import ensure_project_exists
from db.models import Review


async def create_review(
    session: AsyncSession,
    project_id: UUID,
    payload: ReviewCreate,
    reviewer_id: UUID,
) -> ReviewResponse:
    """Create a review for a project.

    Args:
        session: Database session.
        project_id: ID of the project to review.
        payload: Review content and metadata.
        reviewer_id: ID of the authenticated user creating the review.
    """
    await ensure_project_exists(session, project_id)

    review = Review(
        project_id=project_id,
        reviewer_id=reviewer_id,
        content=payload.content,
        target_file=payload.target_file,
        target_component=payload.target_component,
        is_private=payload.is_private,
    )

    session.add(review)
    await session.commit()
    await session.refresh(review)

    return ReviewResponse.model_validate(review, from_attributes=True)


async def list_reviews(
    session: AsyncSession,
    project_id: UUID,
) -> ReviewListResponse:
    """List all reviews for a project."""
    await ensure_project_exists(session, project_id)

    query: Select[tuple[Review]] = (
        select(Review).where(Review.project_id == project_id).order_by(Review.created_at.asc())
    )
    result = await session.execute(query)
    reviews = result.scalars().all()

    return ReviewListResponse(
        project_id=project_id,
        items=[ReviewResponse.model_validate(review, from_attributes=True) for review in reviews],
    )
