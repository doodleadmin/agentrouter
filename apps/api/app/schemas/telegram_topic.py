"""TelegramTopic schemas — create / read / update."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TelegramTopicKind = Literal["general", "agent", "approvals", "system_logs", "task"]

# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

class TelegramTopicCreate(BaseModel):
    """Bind a Telegram forum topic to an agent or project."""

    chat_id: int = Field(..., ge=1)
    message_thread_id: int = Field(..., ge=0)
    title: str = Field(..., max_length=255)
    kind: TelegramTopicKind = Field(
        ...,
        examples=["general", "agent", "approvals", "system_logs", "task"],
    )
    agent_id: UUID | None = None
    project_id: UUID | None = None
    is_active: bool = True

    model_config = ConfigDict(extra="forbid")


class TelegramTopicUpdate(BaseModel):
    """Partial update to a topic binding."""

    title: str | None = Field(None, max_length=255)
    kind: TelegramTopicKind | None = None
    agent_id: UUID | None = None
    project_id: UUID | None = None
    is_active: bool | None = None

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

class TelegramTopicRead(BaseModel):
    """TelegramTopic binding as returned by the API."""

    id: UUID
    chat_id: int
    message_thread_id: int
    title: str
    kind: str
    agent_id: UUID | None
    project_id: UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
