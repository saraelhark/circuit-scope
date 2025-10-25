"""Pydantic schemas for project reviews/comments."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    target_file: str | None = Field(default=None, max_length=255)
    target_component: str | None = Field(default=None, max_length=255)
    is_private: bool = False


class ReviewCreate(ReviewBase):
    reviewer_id: UUID | None = None


class ReviewUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=5000)
    target_file: str | None = Field(default=None, max_length=255)
    target_component: str | None = Field(default=None, max_length=255)
    is_private: bool | None = None


class ReviewResponse(BaseModel):
    id: UUID
    project_id: UUID
    reviewer_id: UUID
    content: str
    target_file: str | None
    target_component: str | None
    is_private: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    project_id: UUID
    items: list[ReviewResponse]


__all__ = [
    "ReviewBase",
    "ReviewCreate",
    "ReviewListResponse",
    "ReviewResponse",
    "ReviewUpdate",
]
