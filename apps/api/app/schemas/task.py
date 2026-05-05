"""Pydantic schemas for Task CRUD and status transitions."""

from __future__ import annotations

import datetime
from typing import Any
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from app.db.enums import RiskLevel, TaskStatus
from app.schemas import BaseModel

# ── valid status transitions ────────────────────────────────────────────

ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.CREATED: {TaskStatus.ROUTED, TaskStatus.PLANNING, TaskStatus.CANCELLED},
    TaskStatus.ROUTED: {TaskStatus.PLANNING, TaskStatus.CANCELLED},
    TaskStatus.PLANNING: {TaskStatus.WAITING_APPROVAL, TaskStatus.APPROVED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.WAITING_APPROVAL: {TaskStatus.APPROVED, TaskStatus.CANCELLED},
    TaskStatus.APPROVED: {TaskStatus.RUNNING, TaskStatus.CANCELLED},
    TaskStatus.RUNNING: {TaskStatus.TESTS_RUNNING, TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.TESTS_RUNNING: {TaskStatus.PR_CREATED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.PR_CREATED: {TaskStatus.DEPLOYING_STAGING, TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.DEPLOYING_STAGING: {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.DEPLOYING_PRODUCTION: {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.FAILED: set(),
    TaskStatus.CANCELLED: set(),
    TaskStatus.COMPLETED: set(),
}


# ── schemas ─────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    """Request body for creating a new task."""

    title: str = Field(min_length=1, max_length=255)
    raw_text: str = Field(min_length=1)
    normalized_text: str = Field(min_length=1)
    risk_level: RiskLevel = RiskLevel.LOW
    intent: str | None = None
    project_id: UUID | None = None
    agent_id: UUID | None = None
    telegram_chat_id: int | None = None
    telegram_thread_id: int | None = None
    created_by: int | None = None

    model_config = ConfigDict(extra="forbid")


class TaskUpdate(BaseModel):
    """Partial update for editable task fields."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    risk_level: RiskLevel | None = None
    intent: str | None = None
    plan_text: str | None = None
    result_summary: str | None = None
    branch_name: str | None = None
    worktree_path: str | None = None
    raw_text: str | None = None
    normalized_text: str | None = None
    payload: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid")


class TaskStatusUpdate(BaseModel):
    """Request body for status transition."""

    status: TaskStatus

    model_config = ConfigDict(extra="forbid")


class TaskPlanRead(BaseModel):
    """Dedicated endpoint response for /tasks/{id}/plan."""

    task_id: UUID
    plan_text: str | None
    plan_version: int = 1
    status: str


class CallbackAnswerIn(BaseModel):
    """Request body for /tasks/{id}/callback-answer validation."""

    callback_data: str = Field(min_length=1, max_length=1024)
    telegram_chat_id: int | None = None
    telegram_thread_id: int | None = None
    telegram_user_id: int | None = None

    model_config = ConfigDict(extra="forbid")


class CallbackAnswerRead(BaseModel):
    """Response for /tasks/{id}/callback-answer with task + approval snapshot."""

    task_id: UUID
    task_status: str
    task_external_id: str
    approval_id: UUID | None = None
    approval_status: str | None = None
    action_valid: bool
    action: str
    error: str | None = None


class TaskRead(BaseModel):
    """Response representation of a task."""

    id: UUID
    external_id: str
    title: str
    raw_text: str
    normalized_text: str
    status: str
    risk_level: str
    intent: str | None
    project_id: UUID | None
    agent_id: UUID | None
    telegram_chat_id: int | None
    telegram_thread_id: int | None
    created_by: int | None
    branch_name: str | None
    worktree_path: str | None
    plan_text: str | None
    result_summary: str | None
    payload: dict[str, Any]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _ensure_aware(cls, v: Any) -> str:
        if isinstance(v, datetime.datetime):
            return v.isoformat()
        return str(v)

    model_config = ConfigDict(from_attributes=True)
