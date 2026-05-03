"""initial all tables

Revision ID: 0001_initial_all_tables
Revises:
Create Date: 2026-05-03 16:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0001_initial_all_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "projects",
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("repo_path", sa.Text(), nullable=False),
        sa.Column("memory_path", sa.Text(), nullable=False),
        sa.Column("default_branch", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("stack", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_projects"),
    )
    op.create_index(op.f("ix_projects_slug"), "projects", ["slug"], unique=True)

    op.create_table(
        "agents",
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("permissions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_agents"),
    )
    op.create_index(op.f("ix_agents_slug"), "agents", ["slug"], unique=True)

    op.create_table(
        "telegram_topics",
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("message_thread_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="SET NULL", name="fk_telegram_topics_agent_id_agents"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL", name="fk_telegram_topics_project_id_projects"),
        sa.PrimaryKeyConstraint("id", name="pk_telegram_topics"),
        sa.UniqueConstraint("chat_id", "message_thread_id", name="uq_telegram_topics_chat_thread"),
    )
    op.create_index(op.f("ix_telegram_topics_chat_id"), "telegram_topics", ["chat_id"], unique=False)
    op.create_index(op.f("ix_telegram_topics_kind"), "telegram_topics", ["kind"], unique=False)

    op.create_table(
        "tasks",
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.Column("intent", sa.String(length=100), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("telegram_thread_id", sa.BigInteger(), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("branch_name", sa.String(length=255), nullable=True),
        sa.Column("worktree_path", sa.Text(), nullable=True),
        sa.Column("plan_text", sa.Text(), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="SET NULL", name="fk_tasks_agent_id_agents"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL", name="fk_tasks_project_id_projects"),
        sa.PrimaryKeyConstraint("id", name="pk_tasks"),
    )
    op.create_index(op.f("ix_tasks_external_id"), "tasks", ["external_id"], unique=True)
    op.create_index(op.f("ix_tasks_status"), "tasks", ["status"], unique=False)
    op.create_index(op.f("ix_tasks_risk_level"), "tasks", ["risk_level"], unique=False)
    op.create_index(op.f("ix_tasks_project_id"), "tasks", ["project_id"], unique=False)
    op.create_index(op.f("ix_tasks_agent_id"), "tasks", ["agent_id"], unique=False)

    op.create_table(
        "approvals",
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("requested_by_agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_by", sa.BigInteger(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["requested_by_agent_id"], ["agents.id"], ondelete="SET NULL", name="fk_approvals_requested_by_agent_id_agents"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE", name="fk_approvals_task_id_tasks"),
        sa.PrimaryKeyConstraint("id", name="pk_approvals"),
    )
    op.create_index("idx_approvals_task", "approvals", ["task_id"], unique=False)
    op.create_index("idx_approvals_status", "approvals", ["status"], unique=False)

    op.create_table(
        "task_events",
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE", name="fk_task_events_task_id_tasks"),
        sa.PrimaryKeyConstraint("id", name="pk_task_events"),
    )
    op.create_index("idx_task_events_task", "task_events", ["task_id"], unique=False)
    op.create_index("idx_task_events_type", "task_events", ["event_type"], unique=False)
    op.create_index("idx_task_events_created", "task_events", ["created_at"], unique=False)

    op.create_table(
        "memory_documents",
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE", name="fk_memory_documents_project_id_projects"),
        sa.PrimaryKeyConstraint("id", name="pk_memory_documents"),
    )
    op.create_index("idx_memory_docs_scope", "memory_documents", ["scope"], unique=False)
    op.create_index(
        "idx_memory_docs_scope_project_path",
        "memory_documents",
        ["scope", "project_id", "path"],
        unique=False,
    )

    op.create_table(
        "memory_chunks",
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(dim=1536), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["memory_documents.id"], ondelete="CASCADE", name="fk_memory_chunks_document_id_memory_documents"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL", name="fk_memory_chunks_project_id_projects"),
        sa.PrimaryKeyConstraint("id", name="pk_memory_chunks"),
    )
    op.create_index("idx_memory_chunks_project", "memory_chunks", ["project_id"], unique=False)
    op.create_index("ix_memory_chunks_document_id", "memory_chunks", ["document_id"], unique=False)
    op.create_index(
        "idx_memory_chunks_embedding",
        "memory_chunks",
        ["embedding"],
        unique=False,
        postgresql_using="ivfflat",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("idx_memory_chunks_embedding", table_name="memory_chunks")
    op.drop_index("ix_memory_chunks_document_id", table_name="memory_chunks")
    op.drop_index("idx_memory_chunks_project", table_name="memory_chunks")
    op.drop_table("memory_chunks")

    op.drop_index("idx_memory_docs_scope_project_path", table_name="memory_documents")
    op.drop_index("idx_memory_docs_scope", table_name="memory_documents")
    op.drop_table("memory_documents")

    op.drop_index("idx_task_events_created", table_name="task_events")
    op.drop_index("idx_task_events_type", table_name="task_events")
    op.drop_index("idx_task_events_task", table_name="task_events")
    op.drop_table("task_events")

    op.drop_index("idx_approvals_status", table_name="approvals")
    op.drop_index("idx_approvals_task", table_name="approvals")
    op.drop_table("approvals")

    op.drop_index(op.f("ix_tasks_agent_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_project_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_risk_level"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_status"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_external_id"), table_name="tasks")
    op.drop_table("tasks")

    op.drop_index(op.f("ix_telegram_topics_kind"), table_name="telegram_topics")
    op.drop_index(op.f("ix_telegram_topics_chat_id"), table_name="telegram_topics")
    op.drop_table("telegram_topics")

    op.drop_index(op.f("ix_agents_slug"), table_name="agents")
    op.drop_table("agents")

    op.drop_index(op.f("ix_projects_slug"), table_name="projects")
    op.drop_table("projects")
