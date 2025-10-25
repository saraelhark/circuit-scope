"""Service layer for project reviews and comments."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.reviews import ReviewCreate, ReviewListResponse, ReviewResponse, ReviewUpdate
from db.models import Project, Review


async def create_review(
    session: AsyncSession,
    project_id: UUID,
    payload: ReviewCreate,
) -> ReviewResponse:
    await _ensure_project_exists(session, project_id)

    review = Review(
        project_id=project_id,
        reviewer_id=payload.reviewer_id,
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
    await _ensure_project_exists(session, project_id)

    query: Select[tuple[Review]] = (
        select(Review)
        .where(Review.project_id == project_id)
        .order_by(Review.created_at.asc())
    )
    result = await session.execute(query)
    reviews = result.scalars().all()

    return ReviewListResponse(
        project_id=project_id,
        items=[ReviewResponse.model_validate(review, from_attributes=True) for review in reviews],
    )


async def update_review(
    session: AsyncSession,
    project_id: UUID,
    review_id: UUID,
    payload: ReviewUpdate,
) -> ReviewResponse:
    review = await _get_review(session, project_id, review_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(review, field, value)

    await session.commit()
    await session.refresh(review)

    return ReviewResponse.model_validate(review, from_attributes=True)


async def delete_review(
    session: AsyncSession,
    project_id: UUID,
    review_id: UUID,
) -> None:
    review = await _get_review(session, project_id, review_id)
    await session.delete(review)
    await session.commit()


async def _ensure_project_exists(session: AsyncSession, project_id: UUID) -> None:
    exists_query = select(Project.id).where(Project.id == project_id)
    result = await session.execute(exists_query)
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


async def _get_review(session: AsyncSession, project_id: UUID, review_id: UUID) -> Review:
    query = (
        select(Review)
        .where(Review.id == review_id, Review.project_id == project_id)
    )
    result = await session.execute(query)
    review = result.scalar_one_or_none()
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return review
