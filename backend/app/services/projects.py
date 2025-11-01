"""Service layer for project management."""

from __future__ import annotations

from typing import Any
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
from app.services.previews import process_project_archive
from app.services.storage.base import StorageService
from db.models import Project, ProjectFile, User


async def _ensure_owner_exists(session: AsyncSession, owner_id: UUID) -> User:
    owner = await session.get(User, owner_id)
    if owner is None:
        owner = User(id=owner_id)
        session.add(owner)
        await session.flush()
    return owner


async def create_project(
    session: AsyncSession,
    storage: StorageService,
    payload: ProjectCreate,
    upload_file: UploadFile | None,
) -> tuple[ProjectResponse, dict[str, Any] | None]:
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
        status=payload.status or "draft",
        github_repo_url=payload.github_repo_url,
        secret_link=None,
    )

    session.add(project)
    await session.flush()

    upload_result: dict[str, Any] | None = None

    if upload_file is not None:
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

        storage_path = f"projects/{project.id}/{filename}"
        try:
            await storage.save(storage_path, upload_file.file)
        finally:
            await upload_file.close()

        project_file = ProjectFile(
            project=project,
            filename=filename,
            file_type="kicad_zip",
            storage_path=storage_path,
        )
        session.add(project_file)
        upload_result = {"filename": filename, "storage_path": storage_path}

        try:
            process_project_archive(storage, project.id, storage_path)
        except Exception:  # noqa: BLE001
            # Failures during preview generation should not block project creation.
            logger = logging.getLogger(__name__)
            logger.exception("Preview generation failed for project %s", project.id)

    try:
        await session.commit()
    except IntegrityError as exc:  # noqa: ASYNC100
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create project"
        ) from exc

    await session.refresh(project, attribute_names=["files"])
    return ProjectResponse.model_validate(project, from_attributes=True), upload_result


async def list_projects(
    session: AsyncSession,
    *,
    page: int,
    size: int,
    only_public: bool | None = None,
    owner_id: UUID | None = None,
) -> ProjectListResponse:
    if page < 1 or size < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pagination parameters",
        )

    query: Select[tuple[Project]] = (
        select(Project)
        .options(selectinload(Project.files))
        .order_by(Project.created_at.desc())
    )

    if only_public is not None:
        query = query.where(Project.is_public.is_(only_public))
    total_query = select(func.count()).select_from(Project)
    if owner_id is not None:
        query = query.where(Project.owner_id == owner_id)
        total_query = total_query.where(Project.owner_id == owner_id)
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
    project = await _get_project_model(session, project_id)
    return ProjectResponse.model_validate(project, from_attributes=True)


async def update_project(
    session: AsyncSession,
    project_id: UUID,
    payload: ProjectUpdate,
) -> ProjectResponse:
    project = await _get_project_model(session, project_id)

    for field, value in payload.model_dump(
        exclude_unset=True, exclude_none=True
    ).items():
        setattr(project, field, value)

    await session.commit()
    await session.refresh(project, attribute_names=["files"])
    return ProjectResponse.model_validate(project, from_attributes=True)


async def delete_project(
    session: AsyncSession,
    storage: StorageService,
    project_id: UUID,
) -> None:
    project = await _get_project_model(session, project_id)

    file_paths = [file.storage_path for file in project.files]

    await session.delete(project)
    await session.commit()

    for path in file_paths:
        try:
            await storage.delete(path)
        except Exception:  # noqa: BLE001
            continue


async def _get_project_model(session: AsyncSession, project_id: UUID) -> Project:
    result = await session.execute(
        select(Project)
        .options(selectinload(Project.files))
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project
