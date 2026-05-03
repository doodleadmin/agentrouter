"""Agent schemas — create / read / update."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

class AgentCreate(BaseModel):
    """Fields required to register a new agent."""

    slug: str = Field(..., max_length=255, examples=["backend"])
    name: str = Field(..., max_length=255)
    role: str = Field(..., min_length=1, max_length=100)
    system_prompt: str = Field(...)
    model: str | None = Field(None, max_length=100)
    permissions: dict = Field(default_factory=dict)
    status: str = Field("active", max_length=50)

    model_config = ConfigDict(extra="forbid")


class AgentUpdate(BaseModel):
    """Partial update for an agent profile."""

    name: str | None = Field(None, max_length=255)
    role: str | None = Field(None, max_length=100)
    system_prompt: str | None = None
    model: str | None = None
    permissions: dict | None = None
    status: str | None = Field(None, max_length=50)

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

class AgentRead(BaseModel):
    """Agent as returned by the API."""

    id: UUID
    slug: str
    name: str
    role: str
    system_prompt: str
    model: str | None
    permissions: dict
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
