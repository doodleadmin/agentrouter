"""Async CRUD service for telegram topics."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telegram_topic import TelegramTopic
from app.schemas.telegram_topic import TelegramTopicCreate, TelegramTopicUpdate


class TelegramTopicService:
    """Encapsulates topic binding persistence logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── mutations ──────────────────────────────────────────────────────

    async def create(self, data: TelegramTopicCreate) -> TelegramTopic:
        obj = TelegramTopic(**data.model_dump())
        self._session.add(obj)
        await self._session.flush()
        return obj

    async def update(self, topic_id: UUID, data: TelegramTopicUpdate) -> TelegramTopic | None:
        changes = data.model_dump(exclude_none=True, exclude_unset=True)
        if not changes:
            return await self.get(topic_id)

        stmt = (
            update(TelegramTopic)
            .where(TelegramTopic.id == topic_id)
            .values(**changes)
            .returning(TelegramTopic)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def deactivate(self, topic_id: UUID) -> TelegramTopic | None:
        """Soft-deactivate: set is_active=False."""
        stmt = (
            update(TelegramTopic)
            .where(TelegramTopic.id == topic_id)
            .values(is_active=False)
            .returning(TelegramTopic)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ── queries ────────────────────────────────────────────────────────

    async def get(self, topic_id: UUID) -> TelegramTopic | None:
        return await self._session.get(TelegramTopic, topic_id)

    async def list(self, *, active_only: bool = False) -> list[TelegramTopic]:
        stmt = select(TelegramTopic).order_by(TelegramTopic.title)
        if active_only:
            stmt = stmt.where(TelegramTopic.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
