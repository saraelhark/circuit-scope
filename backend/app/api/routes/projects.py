"""Project management API routes."""

from __future__ import annotations

import logging
from uuid import UUID
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session, get_storage_service
from app.api.schemas.projects import (
    ProjectCreate,
    ProjectListResponse,
    ProjectPreviewResponse,
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
from app.services.previews import (
    load_preview_index,
    preview_asset_filesystem_path,
)
from app.services.storage.base import StorageService

router = APIRouter()
logger = logging.getLogger(__name__)

_MEDIA_TYPES = {
    ".svg": "image/svg+xml",
    ".glb": "model/gltf-binary",
}


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


@router.get("/{project_id}/previews", response_model=ProjectPreviewResponse)
async def get_project_previews_endpoint(
    project_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    storage: StorageService = Depends(get_storage_service),
) -> ProjectPreviewResponse:
    await get_project(session, project_id)

    try:
        index = load_preview_index(storage, project_id)
    except FileNotFoundError:
        index = {"project": {}, "schematics": [], "layouts": [], "models": []}

    def build_asset_entry(entry: dict[str, Any]) -> dict[str, Any]:
        asset_path = entry.get("path")
        url = (
            str(
                request.url_for(
                    "get_project_preview_asset",
                    project_id=str(project_id),
                    asset_path=asset_path,
                )
            )
            if asset_path
            else None
        )

        enriched = {**entry, "url": url}

        pages = entry.get("pages")
        if isinstance(pages, list):
            enriched["pages"] = [build_asset_entry(page) for page in pages]

        composed = entry.get("composed")
        if isinstance(composed, dict):
            enriched["composed"] = build_asset_entry(composed)

        return enriched

    schematics = [build_asset_entry(entry) for entry in index.get("schematics", [])]
    layouts = [build_asset_entry(entry) for entry in index.get("layouts", [])]
    models = [build_asset_entry(entry) for entry in index.get("models", [])]

    return ProjectPreviewResponse(
        project=index.get("project", {}),
        schematics=schematics,
        layouts=layouts,
        models=models,
    )


@router.get("/{project_id}/previews/{asset_path:path}")
async def get_project_preview_asset(
    project_id: UUID,
    asset_path: str,
    session: AsyncSession = Depends(get_db_session),
    storage: StorageService = Depends(get_storage_service),
):
    await get_project(session, project_id)

    try:
        fs_path = preview_asset_filesystem_path(storage, project_id, asset_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Preview not available"
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to resolve preview asset for project %s", project_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load preview",
        ) from exc

    media_type = _MEDIA_TYPES.get(fs_path.suffix.lower())
    if media_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unsupported preview format"
        )

    return FileResponse(fs_path, media_type=media_type)
