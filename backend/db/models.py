"""SQLAlchemy ORM models for the application database."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID as UUIDType, uuid4

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Float,
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
        TIMESTAMP(timezone=True),
        default=datetime.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime.now(),
        onupdate=datetime.now(),
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
    comment_threads: Mapped[list["CommentThread"]] = relationship(
        back_populates="created_by",
        foreign_keys="CommentThread.created_by_id",
    )
    resolved_comment_threads: Mapped[list["CommentThread"]] = relationship(
        back_populates="resolved_by",
        foreign_keys="CommentThread.resolved_by_id",
        viewonly=True,
    )
    thread_comments: Mapped[list["ThreadComment"]] = relationship(
        back_populates="author"
    )


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
    status: Mapped[str] = mapped_column(String, default="open", nullable=False)

    owner: Mapped[User] = relationship(back_populates="projects")
    reviews: Mapped[list["Review"]] = relationship(back_populates="project")
    comment_threads: Mapped[list["CommentThread"]] = relationship(
        back_populates="project"
    )
    analytics_events: Mapped[list["AnalyticsEvent"]] = relationship(
        back_populates="project"
    )
    files: Mapped[list["ProjectFile"]] = relationship(back_populates="project")


class Review(TimestampMixin, Base):
    __tablename__ = "reviews"
    __table_args__ = (Index("idx_reviews_project", "project_id"),)

    id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
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
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
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
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str | None] = mapped_column(String)
    storage_path: Mapped[str] = mapped_column(String, nullable=False)

    project: Mapped[Project] = relationship(back_populates="files")


class CommentThread(TimestampMixin, Base):
    __tablename__ = "comment_threads"
    __table_args__ = (
        Index("idx_comment_threads_project", "project_id"),
        Index("idx_comment_threads_view", "project_id", "view_id"),
    )

    id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by_id: Mapped[UUIDType | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    view_id: Mapped[str] = mapped_column(String, nullable=False)
    pin_x: Mapped[float] = mapped_column(Float, nullable=False)
    pin_y: Mapped[float] = mapped_column(Float, nullable=False)
    annotation: Mapped[dict | None] = mapped_column(JSON)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_by_id: Mapped[UUIDType | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    project: Mapped[Project] = relationship(back_populates="comment_threads")
    created_by: Mapped[User | None] = relationship(
        back_populates="comment_threads", foreign_keys=[created_by_id]
    )
    resolved_by: Mapped[User | None] = relationship(
        back_populates="resolved_comment_threads", foreign_keys=[resolved_by_id]
    )
    comments: Mapped[list["ThreadComment"]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="ThreadComment.created_at",
    )


class ThreadComment(TimestampMixin, Base):
    __tablename__ = "thread_comments"
    __table_args__ = (Index("idx_thread_comments_thread", "thread_id"),)

    id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    thread_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("comment_threads.id", ondelete="CASCADE"),
        nullable=False,
    )
    author_id: Mapped[UUIDType | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    parent_id: Mapped[UUIDType | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("thread_comments.id", ondelete="CASCADE"),
        nullable=True,
    )
    guest_name: Mapped[str | None] = mapped_column(String(255))
    guest_email: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text, nullable=False)

    thread: Mapped[CommentThread] = relationship(back_populates="comments")
    author: Mapped[User | None] = relationship(
        back_populates="thread_comments", foreign_keys=[author_id]
    )
    parent: Mapped["ThreadComment | None"] = relationship(
        remote_side="ThreadComment.id", back_populates="replies"
    )
    replies: Mapped[list["ThreadComment"]] = relationship(back_populates="parent")


__all__ = [
    "AnalyticsEvent",
    "Base",
    "Project",
    "ProjectFile",
    "Review",
    "User",
    "CommentThread",
    "ThreadComment",
]
