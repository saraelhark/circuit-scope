"""Project management API routes."""

from __future__ import annotations

import logging
import pathlib
from uuid import UUID
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import Response
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session, get_storage_service, get_current_user
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
    run_project_processing_task,
    increment_project_view,
)
from db.models import User
from app.services.previews import (
    load_preview_index,
    save_image_previews_from_uploads,
    validate_preview_asset_path,
)
from app.services.storage.base import StorageService, StorageError

router = APIRouter()
logger = logging.getLogger(__name__)

_MEDIA_TYPES = {
    ".svg": "image/svg+xml",
    ".glb": "model/gltf-binary",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


@router.post("/", response_model=ProjectUploadResponse, status_code=status.HTTP_201_CREATED)
async def create_project_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    project_data: str = Form(..., description="JSON-encoded ProjectCreate payload"),
    upload: UploadFile | None = File(default=None, description="KiCad project ZIP"),
    images: list[UploadFile] | None = File(
        default=None, description="Image previews for image-only projects"
    ),
    session: AsyncSession = Depends(get_db_session),
    storage: StorageService = Depends(get_storage_service),
) -> ProjectUploadResponse:
    """Create a new project."""
    logger.info("Attempting to create project: %s", project_data)
    try:
        payload = ProjectCreate.model_validate_json(project_data)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()
        ) from exc

    # Normalise images list for easier handling
    image_files = images or []

    # Create project row; KiCad projects may include a ZIP archive, image-only
    # projects skip the archive pipeline entirely.
    effective_upload: UploadFile | None = upload if payload.source_type == "kicad" else None
    project_response, upload_path = await create_project(session, payload, effective_upload)

    upload_result: dict[str, Any] | None = None

    if payload.source_type == "kicad" and upload_path:
        background_tasks.add_task(
            run_project_processing_task,
            storage,
            project_response.id,
            upload_path,
        )
        upload_result = {
            "filename": upload.filename if upload else "archive.zip",
            "status": "processing_queued",
        }
    elif payload.source_type == "images":
        # For image-only projects, persist uploaded images as preview photos and
        # write the preview index immediately.
        await save_image_previews_from_uploads(
            storage,
            project_response.id,
            image_files,
        )

    return ProjectUploadResponse(project=project_response, upload_result=upload_result)


@router.get("/", response_model=ProjectListResponse)
async def list_projects_endpoint(
    page: int = 1,
    size: int = 20,
    only_public: bool | None = None,
    owner_id: UUID | None = None,
    status: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> ProjectListResponse:
    """List all projects."""
    logger.info("Attempting to list projects")
    return await list_projects(
        session,
        page=page,
        size=size,
        only_public=only_public,
        owner_id=owner_id,
        status=status,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_endpoint(
    project_id: UUID,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> ProjectResponse:
    """Get a project by ID."""
    # Check for view tracking cookie
    cookie_name = f"viewed_project_{project_id}"
    if not request.cookies.get(cookie_name):
        # Track the view if not already viewed in this session/window
        await increment_project_view(session, project_id)
        # Set cookie to prevent multiple counts (valid for 24 hours)
        response.set_cookie(key=cookie_name, value="true", max_age=86400)

    return await get_project(session, project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project_endpoint(
    project_id: UUID,
    payload: ProjectUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    """Update a project."""
    return await update_project(session, project_id, payload, current_user.id)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_endpoint(
    project_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    storage: StorageService = Depends(get_storage_service),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a project."""
    await delete_project(session, storage, project_id, current_user.id)
    return None


@router.get("/{project_id}/previews", response_model=ProjectPreviewResponse)
async def get_project_previews_endpoint(
    project_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    storage: StorageService = Depends(get_storage_service),
) -> ProjectPreviewResponse:
    """Get project previews."""
    await get_project(session, project_id)

    try:
        index = await load_preview_index(storage, project_id)
    except FileNotFoundError:
        index = {
            "project": {},
            "schematics": [],
            "layouts": [],
            "models": [],
            "photos": [],
        }

    def build_asset_entry(entry: dict[str, Any]) -> dict[str, Any]:
        asset_path = entry.get("path")

        url: str | None = None
        if asset_path:
            generated_url = request.url_for(
                "get_project_preview_asset",
                project_id=str(project_id),
                asset_path=asset_path,
            )
            url = generated_url.path

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
    photos = [build_asset_entry(entry) for entry in index.get("photos", [])]

    return ProjectPreviewResponse(
        project=index.get("project", {}),
        schematics=schematics,
        layouts=layouts,
        models=models,
        photos=photos,
    )


@router.get("/{project_id}/previews/{asset_path:path}")
async def get_project_preview_asset(
    project_id: UUID,
    asset_path: str,
    session: AsyncSession = Depends(get_db_session),
    storage: StorageService = Depends(get_storage_service),
):
    """Get a project preview asset."""
    await get_project(session, project_id)

    try:
        storage_path = await validate_preview_asset_path(project_id, asset_path)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Preview not available"
        ) from exc
    except Exception as exc:
        logger.exception("Failed to resolve preview asset for project %s", project_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load preview",
        ) from exc

    suffix = pathlib.Path(storage_path).suffix.lower()
    media_type = _MEDIA_TYPES.get(suffix)
    if media_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unsupported preview format"
        )

    try:
        content = await storage.read(storage_path)
        return Response(content=content, media_type=media_type)
    except StorageError as exc:
        logger.error("Failed to read asset from storage: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found"
        ) from exc
