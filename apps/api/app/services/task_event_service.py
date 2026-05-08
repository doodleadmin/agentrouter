"""Async service for task event audit trail (immutable, append-only).

SEC-03 Phase 2: payload is redacted before write via centralized redaction.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ActorType
from app.models.task_event import TaskEvent
from app.security.redaction import redact_mapping


class TaskEventService:
    """Encapsulates task event audit logging (create + list only)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        task_id: UUID,
        event_type: str,
        actor_type: ActorType = ActorType.SYSTEM,
        actor_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> TaskEvent:
        safe_payload = redact_mapping(payload or {})
        obj = TaskEvent(
            task_id=task_id,
            event_type=event_type,
            actor_type=actor_type.value,
            actor_id=actor_id,
            payload=safe_payload,  # type: ignore[arg-type]
        )
        self._session.add(obj)
        await self._session.flush()
        return obj

    async def list_by_task(self, task_id: UUID) -> list[TaskEvent]:
        stmt = (
            select(TaskEvent)
            .where(TaskEvent.task_id == task_id)
            .order_by(TaskEvent.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(
        self,
        *,
        task_id: UUID | None = None,
        event_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TaskEvent]:
        stmt = select(TaskEvent).order_by(TaskEvent.created_at.desc())
        if task_id:
            stmt = stmt.where(TaskEvent.task_id == task_id)
        if event_type:
            stmt = stmt.where(TaskEvent.event_type == event_type)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
