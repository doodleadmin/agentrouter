"""Pydantic schemas for Approval domain."""

from __future__ import annotations

import datetime
from typing import Any
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from app.schemas import BaseModel


class ApprovalCreate(BaseModel):
    """Request body for creating an approval request linked to a task."""

    action: str = Field(min_length=1, max_length=100)
    requested_by_agent_id: UUID | None = None
    approved_by: int | None = None
    reason: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class ApprovalDecideIn(BaseModel):
    """Optional reason when approving/rejecting."""

    reason: str | None = None
    approved_by: int | None = None

    model_config = ConfigDict(extra="forbid")


class ApprovalRead(BaseModel):
    """Response representation of an approval."""

    id: UUID
    task_id: UUID
    action: str
    status: str
    requested_by_agent_id: UUID | None
    approved_by: int | None
    reason: str | None
    payload: dict[str, Any]
    decided_at: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @field_validator("created_at", "updated_at", "decided_at", mode="before")
    @classmethod
    def _ensure_aware(cls, v: Any) -> str | None:
        if v is None:
            return None
        if isinstance(v, datetime.datetime):
            return v.isoformat()
        return str(v)

    model_config = ConfigDict(from_attributes=True)
