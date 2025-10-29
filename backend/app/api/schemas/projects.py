"""Pydantic schemas for project management."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = Field(default=None)
    is_public: bool = False
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
    schematic: str | None
    layout: str | None
    view3d: str | None
