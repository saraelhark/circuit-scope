"""Service layer for project management."""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas.projects import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.previews import (
    MAX_KICAD_ARCHIVE_SIZE_BYTES,
    MAX_KICAD_ARCHIVE_SIZE_MB,
    process_project_archive,
)
from app.services.storage.base import StorageService
from db.models import Project, User, AnalyticsEvent
from db.sessions import async_session_factory

logger = logging.getLogger(__name__)


async def increment_project_view(
    session: AsyncSession, project_id: UUID, user_id: UUID | None = None
) -> None:
    """Increment project view count and record analytics event."""
    project = await session.get(Project, project_id)
    if project:
        project.view_count += 1

        event = AnalyticsEvent(
            project_id=project_id,
            event_type="project_view",
            user_id=user_id,
        )
        session.add(event)
        await session.commit()


async def run_project_processing_task(
    storage: StorageService, project_id: UUID, local_zip_path: Path
) -> None:
    """Background task to process project archives."""
    async with async_session_factory() as session:
        try:
            project = await session.get(Project, project_id)
            if not project:
                logger.error("Project %s not found for processing", project_id)
                return

            project.processing_status = "processing"
            await session.commit()

            await process_project_archive(storage, project_id, local_zip_path)

            project.processing_status = "completed"
            project.processing_error = None
            await session.commit()

        except Exception as exc:
            logger.exception("Processing failed for project %s", project_id)
            try:
                await session.rollback()
                project = await session.get(Project, project_id)
                if project:
                    project.processing_status = "failed"
                    project.processing_error = str(exc)
                    await session.commit()
            except Exception:
                logger.exception(
                    "Failed to update error status for project %s", project_id
                )
        finally:
            # Cleanup the temporary ZIP file
            try:
                if local_zip_path.exists():
                    local_zip_path.unlink()
            except OSError:
                logger.warning("Failed to delete temp file %s", local_zip_path)


async def _ensure_owner_exists(session: AsyncSession, owner_id: UUID) -> User:
    owner = await session.get(User, owner_id)
    if owner is None:
        owner = User(id=owner_id)
        session.add(owner)
        await session.flush()
    return owner


async def create_project(
    session: AsyncSession,
    payload: ProjectCreate,
    upload_file: UploadFile | None,
) -> tuple[ProjectResponse, Path | None]:
    """Create a new project."""
    if payload.owner_id is None:
        owner = User()
        session.add(owner)
        await session.flush()
    else:
        owner = await _ensure_owner_exists(session, payload.owner_id)

    project = Project(
        owner_id=owner.id,
        name=payload.name,
        description=payload.description,
        is_public=payload.is_public,
        status=payload.status or "open",
        github_repo_url=payload.github_repo_url,
        secret_link=None,
        tags=payload.tags,
        source_type=payload.source_type or "kicad",
        thumbnail_kind=payload.thumbnail_kind,
    )

    session.add(project)
    await session.flush()

    # Image-only projects skip the KiCad processing pipeline and are considered
    # processed as soon as they are created.
    if project.source_type == "images":
        project.processing_status = "completed"
        project.processing_error = None

    upload_path: Path | None = None

    if upload_file is not None and project.source_type == "kicad":
        filename = upload_file.filename
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must have a name",
            )
        if not filename.lower().endswith(".zip"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only KiCad ZIP archives are supported",
            )

        file_obj = upload_file.file
        size_bytes: int | None = None
        try:
            file_obj.seek(0, os.SEEK_END)
            size_bytes = file_obj.tell()
        except (OSError, AttributeError):
            size_bytes = None
        finally:
            try:
                file_obj.seek(0)
            except (OSError, AttributeError):
                pass

        if size_bytes is not None and size_bytes > MAX_KICAD_ARCHIVE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"KiCad archive must be {MAX_KICAD_ARCHIVE_SIZE_MB} MB or smaller",
            )

        # Save to temporary location for processing
        temp_dir = Path("/tmp/uploads")
        temp_dir.mkdir(parents=True, exist_ok=True)
        upload_path = temp_dir / f"{project.id}_{filename}"

        try:
            with upload_path.open("wb") as buffer:
                shutil.copyfileobj(file_obj, buffer)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save uploaded file",
            ) from exc
        finally:
            await upload_file.close()

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        # Cleanup temp file if commit fails
        if upload_path and upload_path.exists():
            try:
                upload_path.unlink()
            except OSError:
                pass
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create project"
        ) from exc

    await session.refresh(project, attribute_names=["files", "comment_threads"])
    return ProjectResponse.model_validate(project, from_attributes=True), upload_path


async def list_projects(
    session: AsyncSession,
    *,
    page: int,
    size: int,
    only_public: bool | None = None,
    owner_id: UUID | None = None,
    status: str | None = None,
) -> ProjectListResponse:
    """List projects."""
    if page < 1 or size < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pagination parameters",
        )

    query: Select[tuple[Project]] = (
        select(Project)
        .options(selectinload(Project.files), selectinload(Project.comment_threads))
        .order_by(Project.created_at.desc())
    )

    if only_public is not None:
        query = query.where(Project.is_public.is_(only_public))
    total_query = select(func.count(Project.id))  # pylint: disable=not-callable
    if owner_id is not None:
        query = query.where(Project.owner_id == owner_id)
        total_query = total_query.where(Project.owner_id == owner_id)
    if status is not None:
        query = query.where(Project.status == status)
        total_query = total_query.where(Project.status == status)
    if only_public is not None:
        total_query = total_query.where(Project.is_public.is_(only_public))

    total_result = await session.execute(total_query)
    total = total_result.scalar_one() or 0

    offset = (page - 1) * size
    project_result = await session.execute(query.offset(offset).limit(size))
    projects = project_result.scalars().all()

    return ProjectListResponse(
        items=[
            ProjectResponse.model_validate(project, from_attributes=True)
            for project in projects
        ],
        total=total,
        page=page,
        size=size,
    )


async def get_project(session: AsyncSession, project_id: UUID) -> ProjectResponse:
    """Get a project."""
    project = await get_project_orm_model(session, project_id)
    return ProjectResponse.model_validate(project, from_attributes=True)


async def update_project(
    session: AsyncSession,
    project_id: UUID,
    payload: ProjectUpdate,
) -> ProjectResponse:
    """Update a project."""
    project = await get_project_orm_model(session, project_id)

    for field, value in payload.model_dump(
        exclude_unset=True, exclude_none=True
    ).items():
        setattr(project, field, value)

    await session.commit()
    await session.refresh(project, attribute_names=["files", "comment_threads"])
    return ProjectResponse.model_validate(project, from_attributes=True)


async def delete_project(
    session: AsyncSession,
    storage: StorageService,
    project_id: UUID,
) -> None:
    """Delete a project."""
    project = await get_project_orm_model(session, project_id)

    file_paths = [file.storage_path for file in project.files]

    await session.delete(project)
    await session.commit()

    for path in file_paths:
        try:
            await storage.delete(path)
        except Exception:
            continue


async def get_project_orm_model(session: AsyncSession, project_id: UUID) -> Project:
    """Get a project model."""
    result = await session.execute(
        select(Project)
        .options(selectinload(Project.files), selectinload(Project.comment_threads))
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


async def ensure_project_exists(session: AsyncSession, project_id: UUID) -> None:
    """Ensure a project exists."""
    query = select(Project.id).where(Project.id == project_id)
    result = await session.execute(query)
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
