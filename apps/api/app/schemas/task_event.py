"""Pydantic schemas for TaskEvent audit trail."""

from __future__ import annotations

import datetime
from typing import Any
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from app.schemas import BaseModel

# ── Allowed event types ───────────────────────────────────────────────

ALLOWED_EVENT_TYPES: frozenset[str] = frozenset([
    "message_received",
    "agent_selected",
    "project_selected",
    "memory_retrieved",
    "plan_generated",
    "approval_requested",
    "approval_granted",
    "approval_rejected",
    "worktree_created",
    "command_started",
    "command_finished",
    "file_changed",
    "tests_passed",
    "tests_failed",
    "pr_created",
    "deploy_started",
    "deploy_finished",
    "task_completed",
    "task_failed",
    "task_cancelled",
    "security_violation",
    "sandbox_timeout",
    "sandbox_error",
    "runtime_session_created",
    "runtime_event_received",
    "policy_blocked",
    "runtime_error",
    "runtime_timeout",
    "runtime_retry_scheduled",
    "runtime_duplicate_event_ignored",
    "runtime_event_malformed",
])


# ── Schemas ───────────────────────────────────────────────────────────


class TaskEventCreate(BaseModel):
    """Request body for creating a task event (system/internal use)."""

    event_type: str
    actor_type: str = "system"
    actor_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_type")
    @classmethod
    def _validate_event_type(cls, v: str) -> str:
        if v not in ALLOWED_EVENT_TYPES:
            raise ValueError(
                f"Invalid event_type: '{v}'. "
                f"Allowed types: {sorted(ALLOWED_EVENT_TYPES)}"
            )
        return v


class TaskEventRead(BaseModel):
    """Response representation of a task event."""

    id: UUID
    task_id: UUID
    event_type: str
    actor_type: str
    actor_id: str | None
    payload: dict[str, Any]
    created_at: datetime.datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def _ensure_aware(cls, v: Any) -> str:
        if isinstance(v, datetime.datetime):
            return v.isoformat()
        return str(v)

    model_config = ConfigDict(from_attributes=True)
