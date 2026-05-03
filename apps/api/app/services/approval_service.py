"""Async service for approval lifecycle: create → approve/reject."""

from __future__ import annotations

import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ActorType, ApprovalStatus
from app.models.approval import Approval
from app.schemas.approval import ApprovalCreate, ApprovalDecideIn
from app.services.task_event_service import TaskEventService


class ApprovalService:
    """Encapsulates approval workflow (pending → approved/rejected)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── helpers ─────────────────────────────────────────────────────────

    async def _log_event(
        self, task_id: UUID, event_type: str, actor_type: ActorType, actor_id: str | None
    ) -> None:
        await TaskEventService(self._session).create(
            task_id=task_id,
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
        )

    async def _ensure_pending(self, approval: Approval) -> None:
        if approval.status != ApprovalStatus.PENDING.value:
            raise ValueError(
                f"Approval already decided: {approval.status}"
            )

    # ── mutations ──────────────────────────────────────────────────────

    async def create_request(
        self, task_id: UUID, data: ApprovalCreate
    ) -> Approval:
        obj = Approval(task_id=task_id, **data.model_dump())
        self._session.add(obj)
        await self._session.flush()

        await self._log_event(
            task_id, "approval_requested", ActorType.AGENT,
            str(data.requested_by_agent_id) if data.requested_by_agent_id else None,
        )
        return obj

    async def approve(
        self, approval_id: UUID, data: ApprovalDecideIn | None = None
    ) -> Approval:
        approval = await self._session.get(Approval, approval_id)
        if approval is None:
            raise KeyError("Approval not found")
        await self._ensure_pending(approval)

        reason = data.reason if data else None
        approved_by = data.approved_by if data else None

        stmt = (
            update(Approval)
            .where(Approval.id == approval_id)
            .values(
                status=ApprovalStatus.APPROVED.value,
                reason=reason,
                approved_by=approved_by,
                decided_at=datetime.datetime.now(datetime.timezone.utc),
            )
            .returning(Approval)
        )
        result = await self._session.execute(stmt)
        updated = result.scalar_one()

        await self._log_event(
            updated.task_id, "approval_granted", ActorType.USER,
            str(approved_by) if approved_by else None,
        )
        return updated

    async def reject(
        self, approval_id: UUID, data: ApprovalDecideIn | None = None
    ) -> Approval:
        approval = await self._session.get(Approval, approval_id)
        if approval is None:
            raise KeyError("Approval not found")
        await self._ensure_pending(approval)

        reason = data.reason if data else None
        approved_by = data.approved_by if data else None

        stmt = (
            update(Approval)
            .where(Approval.id == approval_id)
            .values(
                status=ApprovalStatus.REJECTED.value,
                reason=reason,
                approved_by=approved_by,
                decided_at=datetime.datetime.now(datetime.timezone.utc),
            )
            .returning(Approval)
        )
        result = await self._session.execute(stmt)
        updated = result.scalar_one()

        await self._log_event(
            updated.task_id, "approval_rejected", ActorType.USER,
            str(approved_by) if approved_by else None,
        )
        return updated

    # ── queries ────────────────────────────────────────────────────────

    async def get(self, approval_id: UUID) -> Approval | None:
        return await self._session.get(Approval, approval_id)

    async def list_by_task(self, task_id: UUID) -> list[Approval]:
        stmt = (
            select(Approval)
            .where(Approval.task_id == task_id)
            .order_by(Approval.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
