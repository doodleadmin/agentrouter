"""Async CRUD service for agents."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate


class AgentService:
    """Encapsulates agent persistence logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── mutations ──────────────────────────────────────────────────────

    async def create(self, data: AgentCreate) -> Agent:
        obj = Agent(**data.model_dump())
        self._session.add(obj)
        await self._session.flush()
        return obj

    async def update(self, agent_id: UUID, data: AgentUpdate) -> Agent | None:
        changes = data.model_dump(exclude_none=True, exclude_unset=True)
        if not changes:
            return await self.get(agent_id)

        stmt = (
            update(Agent)
            .where(Agent.id == agent_id)
            .values(**changes)
            .returning(Agent)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def disable(self, agent_id: UUID) -> Agent | None:
        """Soft-disable: change status to 'disabled'."""
        stmt = (
            update(Agent)
            .where(Agent.id == agent_id)
            .values(status="disabled")
            .returning(Agent)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ── queries ────────────────────────────────────────────────────────

    async def get(self, agent_id: UUID) -> Agent | None:
        return await self._session.get(Agent, agent_id)

    async def list(self, *, active_only: bool = False) -> list[Agent]:
        stmt = select(Agent).order_by(Agent.name)
        if active_only:
            stmt = stmt.where(Agent.status == "active")
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
