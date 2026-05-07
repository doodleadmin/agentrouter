"""Security audit event model — append-only trail for security decisions.

Never updated or deleted. Best-effort recording available.
"""

from datetime import datetime
from uuid import UUID as _UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin


class SecurityAuditEvent(Base, UUIDPrimaryKeyMixin):
    """Append-only security audit trail. Never updated or deleted."""

    __tablename__ = "security_audit_events"
    __table_args__ = (
        Index("idx_audit_task", "task_id"),
        Index("idx_audit_event_type", "event_type"),
        Index("idx_audit_actor", "actor_type", "actor_id"),
        Index("idx_audit_decision", "decision"),
        Index("idx_audit_created", "created_at"),
    )

    # ── Core event identification ───────────────────────────────────────
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    action: Mapped[str | None] = mapped_column(String(100), nullable=True)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    audit_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── FK references (all nullable; SET NULL on delete) ────────────────
    task_id: Mapped[str | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    approval_id: Mapped[str | None] = mapped_column(
        ForeignKey("approvals.id", ondelete="SET NULL"), nullable=True
    )
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    agent_id: Mapped[str | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )

    # ── Telegram context ────────────────────────────────────────────────
    chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    thread_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # ── Privacy-safe metadata ───────────────────────────────────────────
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    correlation_id: Mapped[_UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # ── Extensible payload ──────────────────────────────────────────────
    audit_metadata: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict, server_default="{}"
    )
    error_code: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # ── Timestamp (append-only; no updated_at) ──────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
