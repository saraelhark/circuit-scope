"""Pydantic schemas for annotation comment threads."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator


class ThreadAnnotation(BaseModel):
    """Annotation metadata describing supplemental drawing around a pin."""

    tool: Literal["pin", "circle", "arrow"]
    data: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_annotation(self) -> "ThreadAnnotation":
        if self.tool == "pin":
            self.data = {}
            return self

        if self.tool == "circle":
            radius = self.data.get("radius")
            if radius is None:
                raise ValueError("Circle annotations require a radius value.")
            try:
                radius_value = float(radius)
            except (TypeError, ValueError) as exc:
                raise ValueError("Circle radius must be a number.") from exc
            if not 0 < radius_value <= 0.5:
                raise ValueError("Circle radius must be between 0 and 0.5 (relative to image width).")
            self.data = {"radius": radius_value}
            return self

        if self.tool == "arrow":
            target_x = self.data.get("target_x")
            target_y = self.data.get("target_y")
            if target_x is None or target_y is None:
                raise ValueError("Arrow annotations require target_x and target_y values.")
            try:
                tx = float(target_x)
                ty = float(target_y)
            except (TypeError, ValueError) as exc:
                raise ValueError("Arrow targets must be numeric coordinates.") from exc
            if not 0 <= tx <= 1 or not 0 <= ty <= 1:
                raise ValueError("Arrow target coordinates must be between 0 and 1.")
            self.data = {"target_x": tx, "target_y": ty}
            return self

        raise ValueError("Unsupported annotation tool")


class ThreadCommentBase(BaseModel):
    """Shared fields for comments within a thread."""

    content: str = Field(..., min_length=1, max_length=5000)
    parent_id: UUID | None = None
    author_id: UUID | None = None
    guest_name: str | None = Field(default=None, max_length=255)
    guest_email: EmailStr | None = None

    @model_validator(mode="after")
    def validate_author_sources(self) -> "ThreadCommentBase":
        if self.author_id is None and self.guest_name is None and self.guest_email is None:
            msg = "Either author_id or guest guest_name/email must be provided."
            raise ValueError(msg)
        if self.guest_name is None and self.guest_email is not None:
            msg = "Guest comments require both name and email."
            raise ValueError(msg)
        if self.guest_name is not None and self.guest_email is None:
            msg = "Guest comments require both name and email."
            raise ValueError(msg)
        return self


class ThreadCommentCreate(ThreadCommentBase):
    """Payload for creating a new comment within a thread."""

    pass


class InitialThreadComment(ThreadCommentBase):
    """Initial comment used when creating a thread."""

    parent_id: UUID | None = Field(default=None)

    @model_validator(mode="after")
    def ensure_no_parent(self) -> "InitialThreadComment":
        if self.parent_id is not None:
            msg = "Initial thread comment cannot have a parent."
            raise ValueError(msg)
        return self


class CommentThreadCreate(BaseModel):
    """Payload for creating a new comment thread on a project asset view."""

    view_id: str = Field(..., min_length=1, max_length=100)
    pin_x: float = Field(..., ge=-100000, le=100000)
    pin_y: float = Field(..., ge=-100000, le=100000)
    annotation: ThreadAnnotation | None = None
    created_by_id: UUID | None = None
    initial_comment: InitialThreadComment


class ThreadResolutionUpdate(BaseModel):
    """Payload for updating the resolution status of a thread."""

    is_resolved: bool
    resolved_by_id: UUID | None = None


class ThreadCommentResponse(BaseModel):
    id: UUID
    thread_id: UUID
    parent_id: UUID | None
    author_id: UUID | None
    guest_name: str | None
    guest_email: str | None
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommentThreadResponse(BaseModel):
    id: UUID
    project_id: UUID
    view_id: str
    pin_x: float
    pin_y: float
    annotation: ThreadAnnotation | None
    is_resolved: bool
    created_by_id: UUID | None
    resolved_by_id: UUID | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime
    comments: list[ThreadCommentResponse]
    comment_count: int

    class Config:
        from_attributes = True


class CommentThreadListResponse(BaseModel):
    project_id: UUID
    items: list[CommentThreadResponse]
    total_count: int
    open_count: int
    resolved_count: int


__all__ = [
    "CommentThreadCreate",
    "CommentThreadListResponse",
    "CommentThreadResponse",
    "InitialThreadComment",
    "ThreadAnnotation",
    "ThreadCommentCreate",
    "ThreadCommentResponse",
    "ThreadResolutionUpdate",
]
