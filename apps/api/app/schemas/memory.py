"""Schemas for memory provisioning and CRUD operations."""

from __future__ import annotations

from pydantic import BaseModel, Field, computed_field

# ── Provisioning schemas ──────────────────────────────────────────────


class MemoryProvisionRequest(BaseModel):
    """Request to provision memory for a new project."""

    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
    name: str = Field(..., min_length=1, max_length=200)


class MemoryFileResult(BaseModel):
    """Result for a single file during provisioning."""

    filename: str
    status: str  # "created" | "skipped"
    path: str


class MemoryProvisionResult(BaseModel):
    """Result of provisioning a project memory vault."""

    slug: str
    project_dir: str
    files: list[MemoryFileResult]

    @computed_field
    @property
    def created_count(self) -> int:
        return sum(1 for f in self.files if f.status == "created")

    @computed_field
    @property
    def skipped_count(self) -> int:
        return sum(1 for f in self.files if f.status == "skipped")


class MemoryProjectInfo(BaseModel):
    """Info about an existing project's memory vault."""

    slug: str
    project_dir: str
    files: list[str]
    exists: bool


# ── CRUD schemas ──────────────────────────────────────────────────────


class MemoryFileRead(BaseModel):
    """Response for reading a memory file."""

    path: str
    content: str
    size: int
    modified_at: str


class MemoryFileWriteRequest(BaseModel):
    """Request body for writing/appending to a memory file."""

    content: str = Field(..., min_length=1, max_length=1_000_000)


class MemoryFileWrite(BaseModel):
    """Response for writing/appending a memory file."""

    path: str
    status: str  # "written" | "appended"
    access_tier: str  # "free" | "approval_required" | "forbidden"


class MemoryFileListResult(BaseModel):
    """Response for listing memory files."""

    files: list[str]
    total: int
    prefix: str | None = None
    project_slug: str | None = None


class MemoryAccessInfo(BaseModel):
    """Access tier info for a path."""

    path: str
    access_tier: str  # "free" | "approval_required" | "forbidden"


# ── Retrieval / indexing schemas ──────────────────────────────────────


class MemorySearchRequest(BaseModel):
    """Request for memory semantic search."""

    query: str = Field(..., min_length=1, max_length=2000)
    project_slug: str | None = Field(default=None, max_length=100)
    limit: int = Field(default=5, ge=1, le=50)
    scope: list[str] | None = None


class MemorySearchItem(BaseModel):
    """Single search result item."""

    path: str
    title: str | None = None
    scope: str
    project_slug: str | None = None
    heading: str | None = None
    chunk_index: int
    content: str
    score: float


class MemorySearchResponse(BaseModel):
    """Search response payload."""

    query: str
    total: int
    items: list[MemorySearchItem]


class MemoryReindexRequest(BaseModel):
    """Manual memory reindex request."""

    scope: str = Field(default="all")
    project_slug: str | None = None


class MemoryReindexResponse(BaseModel):
    """Memory reindex operation result."""

    scope: str
    project_slug: str | None = None
    scanned_files: int
    indexed_documents: int
    skipped_documents: int
    total_chunks: int


# ── Forbidden content detection ───────────────────────────────────────

# Forbidden patterns — never write these to memory
FORBIDDEN_PATTERNS: list[str] = [
    "password=",
    "password:",
    'password"',
    "password'",
    "secret=",
    "secret:",
    'secret"',
    "secret'",
    "api_key=",
    "api_key:",
    'api_key"',
    "api_key'",
    "apikey=",
    "apikey:",
    'apikey"',
    "apikey'",
    "private_key=",
    "private_key:",
    'private_key"',
    "private_key'",
    "credential=",
    "credential:",
    'credential"',
    "credential'",
    "auth_token=",
    "auth_token:",
    "access_token=",
    "access_token:",
    "refresh_token=",
    "refresh_token:",
    "session_id=",
    "session_id:",
    "bearer ",
    "bearer_",
    "-----begin private",
    "-----begin rsa",
]


def contains_forbidden_content(text: str) -> bool:
    """Check if text contains potentially secret content that should not be written to memory."""
    text_lower = text.lower()
    return any(pattern in text_lower for pattern in FORBIDDEN_PATTERNS)
