"""Async CRUD service for tasks with lifecycle enforcement."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import TaskStatus
from app.models.task import Task
from app.schemas.task import ALLOWED_TRANSITIONS, TaskCreate, TaskStatusUpdate, TaskUpdate


class TaskService:
    """Encapsulates task persistence and lifecycle logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── external_id counter ─────────────────────────────────────────────

    async def _next_external_id(self) -> str:
        stmt = select(Task.external_id).order_by(Task.created_at.desc()).limit(1)
        result = await self._session.execute(stmt)
        last = result.scalar_one_or_none()
        if last is None:
            return "task-0001"
        try:
            num = int(last.split("-", 1)[1]) + 1
        except (IndexError, ValueError):
            num = 1
        return f"task-{num:04d}"

    # ── mutations ──────────────────────────────────────────────────────

    async def create(self, data: TaskCreate) -> Task:
        obj = Task(
            external_id=await self._next_external_id(),
            **data.model_dump(),
        )
        self._session.add(obj)
        await self._session.flush()
        return obj

    async def update(self, task_id: UUID, data: TaskUpdate) -> Task | None:
        changes = data.model_dump(exclude_none=True, exclude_unset=True)
        if not changes:
            return await self.get(task_id)

        stmt = (
            update(Task)
            .where(Task.id == task_id)
            .values(**changes)
            .returning(Task)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(self, task_id: UUID, data: TaskStatusUpdate) -> Task:
        """Update status with transition validation. Raises ValueError on illegal transition."""
        task = await self.get(task_id)
        if task is None:
            raise KeyError("Task not found")

        current = TaskStatus(task.status)
        target = data.status

        if target not in ALLOWED_TRANSITIONS.get(current, set()):
            raise ValueError(
                f"Illegal transition from {current.value} to {target.value}"
            )

        stmt = (
            update(Task)
            .where(Task.id == task_id)
            .values(status=target.value)
            .returning(Task)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def cancel(self, task_id: UUID) -> Task:
        """Cancel a task if not already in a terminal state."""
        task = await self.get(task_id)
        if task is None:
            raise KeyError("Task not found")

        current = TaskStatus(task.status)
        if current in (TaskStatus.CANCELLED, TaskStatus.COMPLETED, TaskStatus.FAILED):
            return task  # already terminal

        stmt = (
            update(Task)
            .where(Task.id == task_id)
            .values(status=TaskStatus.CANCELLED.value)
            .returning(Task)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    # ── queries ────────────────────────────────────────────────────────

    async def get(self, task_id: UUID) -> Task | None:
        return await self._session.get(Task, task_id)

    async def list(
        self,
        *,
        status: str | None = None,
        project_id: UUID | None = None,
        agent_id: UUID | None = None,
        risk_level: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Task]:
        stmt = select(Task).order_by(Task.created_at.desc())
        if status:
            stmt = stmt.where(Task.status == status)
        if project_id:
            stmt = stmt.where(Task.project_id == project_id)
        if agent_id:
            stmt = stmt.where(Task.agent_id == agent_id)
        if risk_level:
            stmt = stmt.where(Task.risk_level == risk_level)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
