"""add security_audit_events table

Revision ID: 0002_add_security_audit_events
Revises: 0001_initial_all_tables
Create Date: 2026-05-08 10:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0002_add_security_audit_events"
down_revision: Union[str, None] = "0001_initial_all_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "security_audit_events",
        # ── Core event identification ───────────────────────────────────
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=True),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("audit_code", sa.String(length=64), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        # ── FK references (all nullable; SET NULL on delete) ────────────
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approval_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        # ── Telegram context ────────────────────────────────────────────
        sa.Column("chat_id", sa.BigInteger(), nullable=True),
        sa.Column("thread_id", sa.BigInteger(), nullable=True),
        # ── Privacy-safe metadata ───────────────────────────────────────
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        # ── Extensible payload ──────────────────────────────────────────
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("error_code", sa.String(length=32), nullable=True),
        # ── Timestamp (append-only; no updated_at) ──────────────────────
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        # ── PK ──────────────────────────────────────────────────────────
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_security_audit_events"),
        # ── FK constraints ──────────────────────────────────────────────
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="SET NULL", name="fk_audit_task_id_tasks"),
        sa.ForeignKeyConstraint(["approval_id"], ["approvals.id"], ondelete="SET NULL", name="fk_audit_approval_id_approvals"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL", name="fk_audit_project_id_projects"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="SET NULL", name="fk_audit_agent_id_agents"),
    )
    op.create_index("idx_audit_task", "security_audit_events", ["task_id"], unique=False)
    op.create_index("idx_audit_event_type", "security_audit_events", ["event_type"], unique=False)
    op.create_index("idx_audit_actor", "security_audit_events", ["actor_type", "actor_id"], unique=False)
    op.create_index("idx_audit_decision", "security_audit_events", ["decision"], unique=False)
    op.create_index("idx_audit_created", "security_audit_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_audit_created", table_name="security_audit_events")
    op.drop_index("idx_audit_decision", table_name="security_audit_events")
    op.drop_index("idx_audit_actor", table_name="security_audit_events")
    op.drop_index("idx_audit_event_type", table_name="security_audit_events")
    op.drop_index("idx_audit_task", table_name="security_audit_events")
    op.drop_table("security_audit_events")
