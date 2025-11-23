"""Pydantic schemas for project management."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = Field(default=None)
    is_public: bool = True
    status: str | None = Field(default=None, max_length=50)
    github_repo_url: str | None = Field(default=None, max_length=500)


class ProjectCreate(ProjectBase):
    owner_id: UUID | None = Field(default=None)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None)
    is_public: bool | None = None
    status: str | None = Field(default=None, max_length=50)
    github_repo_url: str | None = Field(default=None, max_length=500)


class ProjectFileResponse(BaseModel):
    id: UUID
    filename: str
    file_type: str | None
    storage_path: str
    created_at: datetime


class ProjectResponse(ProjectBase):
    id: UUID
    owner_id: UUID
    processing_status: str
    processing_error: str | None = None
    view_count: int = 0
    open_comment_count: int = 0
    total_comment_count: int = 0
    created_at: datetime
    updated_at: datetime
    files: list[ProjectFileResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    size: int


class ProjectUploadResponse(BaseModel):
    project: ProjectResponse
    upload_result: dict[str, Any] | None = None


class ProjectPreviewResponse(BaseModel):
    project: dict[str, Any]
    schematics: list[dict[str, Any]]
    layouts: list[dict[str, Any]]
    models: list[dict[str, Any]]
