"""Projects router — CRUD with soft-archive."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


# ── helpers ────────────────────────────────────────────────────────────

def _svc(s: AsyncSession = Depends(get_async_session)) -> ProjectService:
    return ProjectService(s)


_PROJECT_404 = "Project not found"


# ── endpoints ──────────────────────────────────────────────────────────


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    svc: ProjectService = Depends(_svc),
) -> ProjectRead:
    return ProjectRead.model_validate(await svc.create(body))


@router.get("", response_model=list[ProjectRead])
async def list_projects(
    active_only: bool = Query(False),
    svc: ProjectService = Depends(_svc),
) -> list[ProjectRead]:
    results = await svc.list(active_only=active_only)
    return [ProjectRead.model_validate(r) for r in results]


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: UUID,
    svc: ProjectService = Depends(_svc),
) -> ProjectRead:
    obj = await svc.get(project_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=_PROJECT_404)
    return ProjectRead.model_validate(obj)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    body: ProjectUpdate,
    svc: ProjectService = Depends(_svc),
) -> ProjectRead:
    obj = await svc.update(project_id, body)
    if obj is None:
        raise HTTPException(status_code=404, detail=_PROJECT_404)
    return ProjectRead.model_validate(obj)


@router.delete("/{project_id}", response_model=ProjectRead, status_code=status.HTTP_200_OK)
async def archive_project(
    project_id: UUID,
    svc: ProjectService = Depends(_svc),
) -> ProjectRead:
    obj = await svc.archive(project_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=_PROJECT_404)
    return ProjectRead.model_validate(obj)
