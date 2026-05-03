"""Project schemas — create / read / update."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    """Fields required to register a new project."""

    slug: str = Field(..., min_length=1, max_length=255, examples=["academy-bot"])
    name: str = Field(..., max_length=255)
    repo_path: str = Field(..., examples=["/opt/repos/academy-bot"])
    memory_path: str = Field(..., examples=[".ai_memory/projects/academy-bot"])
    default_branch: str = Field("main", max_length=100)
    status: str = Field("active", max_length=50)
    stack: dict = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class ProjectUpdate(BaseModel):
    """Partial update — only supplied fields are changed."""

    name: str | None = Field(None, max_length=255)
    repo_path: str | None = None
    memory_path: str | None = None
    default_branch: str | None = Field(None, max_length=100)
    status: str | None = Field(None, max_length=50)
    stack: dict | None = None

    model_config = ConfigDict(extra="forbid")


class ProjectArchive(BaseModel):
    """Soft-archive payload."""

    status: str = Field("archived", max_length=50)

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

class ProjectRead(BaseModel):
    """Project as returned by the API."""

    id: UUID
    slug: str
    name: str
    repo_path: str
    memory_path: str
    default_branch: str
    status: str
    stack: dict
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
