"""Task event model for audit trail."""

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.enums import ActorType


class TaskEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Immutable event log item for each task operation."""

    __tablename__ = "task_events"
    __table_args__ = (
        Index("idx_task_events_task", "task_id"),
        Index("idx_task_events_type", "event_type"),
        Index("idx_task_events_created", "created_at"),
    )

    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False, default=ActorType.SYSTEM.value)
    actor_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
