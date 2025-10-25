"""SQLAlchemy ORM models for the application database."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID as UUIDType, uuid4

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarative class for all models."""


class TimestampMixin:
    """Mixin providing created/updated timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str | None] = mapped_column(String, unique=True)
    display_name: Mapped[str | None] = mapped_column(String)
    avatar_url: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    projects: Mapped[list["Project"]] = relationship(back_populates="owner")
    reviews: Mapped[list["Review"]] = relationship(back_populates="reviewer")


class Project(TimestampMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("secret_link", name="uq_projects_secret_link"),
        Index("idx_projects_public", "is_public"),
    )

    id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    owner_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    kicad_zip_path: Mapped[str | None] = mapped_column(String)
    github_repo_url: Mapped[str | None] = mapped_column(String)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    secret_link: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="draft", nullable=False)

    owner: Mapped[User] = relationship(back_populates="projects")
    reviews: Mapped[list["Review"]] = relationship(back_populates="project")
    analytics_events: Mapped[list["AnalyticsEvent"]] = relationship(back_populates="project")
    files: Mapped[list["ProjectFile"]] = relationship(back_populates="project")


class Review(TimestampMixin, Base):
    __tablename__ = "reviews"
    __table_args__ = (Index("idx_reviews_project", "project_id"),)

    id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    reviewer_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    target_file: Mapped[str | None] = mapped_column(String)
    target_component: Mapped[str | None] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    project: Mapped[Project] = relationship(back_populates="reviews")
    reviewer: Mapped[User] = relationship(back_populates="reviews")


class AnalyticsEvent(Base):
    __tablename__ = "analytics"
    __table_args__ = (
        Index("idx_analytics_project", "project_id"),
        Index("idx_analytics_event", "event_type"),
    )

    id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    event_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False
    )
    user_id: Mapped[UUIDType | None] = mapped_column(UUID(as_uuid=True))
    meta: Mapped[dict | None] = mapped_column(JSON)

    project: Mapped[Project] = relationship(back_populates="analytics_events")


class ProjectFile(TimestampMixin, Base):
    __tablename__ = "project_files"
    __table_args__ = (
        UniqueConstraint("project_id", "filename"),
        Index("idx_project_files_project", "project_id"),
    )

    id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str | None] = mapped_column(String)
    storage_path: Mapped[str] = mapped_column(String, nullable=False)

    project: Mapped[Project] = relationship(back_populates="files")


__all__ = [
    "AnalyticsEvent",
    "Base",
    "Project",
    "ProjectFile",
    "Review",
    "User",
]
