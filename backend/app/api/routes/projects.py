"""Project management API routes."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session, get_storage_service
from app.api.schemas.projects import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
    ProjectUploadResponse,
)
from app.services.projects import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)
from app.services.storage.base import StorageService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/", response_model=ProjectUploadResponse, status_code=status.HTTP_201_CREATED
)
async def create_project_endpoint(
    project_data: str = Form(..., description="JSON-encoded ProjectCreate payload"),
    upload: UploadFile | None = File(default=None, description="KiCad project ZIP"),
    session: AsyncSession = Depends(get_db_session),
    storage: StorageService = Depends(get_storage_service),
) -> ProjectUploadResponse:
    logger.info("Attempting to create project: %s", project_data)
    try:
        payload = ProjectCreate.model_validate_json(project_data)
    except ValidationError as exc:  # pragma: no cover - request validation path
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()
        ) from exc

    project_response, upload_result = await create_project(
        session, storage, payload, upload
    )
    return ProjectUploadResponse(project=project_response, upload_result=upload_result)


@router.get("/", response_model=ProjectListResponse)
async def list_projects_endpoint(
    page: int = 1,
    size: int = 20,
    only_public: bool | None = None,
    owner_id: UUID | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> ProjectListResponse:
    logger.info("Attempting to list projects")
    return await list_projects(
        session, page=page, size=size, only_public=only_public, owner_id=owner_id
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_endpoint(
    project_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ProjectResponse:
    return await get_project(session, project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project_endpoint(
    project_id: UUID,
    payload: ProjectUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ProjectResponse:
    return await update_project(session, project_id, payload)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_endpoint(
    project_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    storage: StorageService = Depends(get_storage_service),
) -> None:
    await delete_project(session, storage, project_id)
    return None
