"""Async CRUD service for projects."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Encapsulates project persistence logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── mutations ──────────────────────────────────────────────────────

    async def create(self, data: ProjectCreate) -> Project:
        obj = Project(**data.model_dump())
        self._session.add(obj)
        await self._session.flush()
        return obj

    async def update(self, project_id: UUID, data: ProjectUpdate) -> Project | None:
        changes = data.model_dump(exclude_none=True, exclude_unset=True)
        if not changes:
            return await self.get(project_id)

        stmt = (
            update(Project)
            .where(Project.id == project_id)
            .values(**changes)
            .returning(Project)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def archive(self, project_id: UUID) -> Project | None:
        """Soft-archive: change status to 'archived'."""
        stmt = (
            update(Project)
            .where(Project.id == project_id)
            .values(status="archived")
            .returning(Project)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ── queries ────────────────────────────────────────────────────────

    async def get(self, project_id: UUID) -> Project | None:
        return await self._session.get(Project, project_id)

    async def list(self, *, active_only: bool = False) -> list[Project]:
        stmt = select(Project).order_by(Project.name)
        if active_only:
            stmt = stmt.where(Project.status == "active")
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
