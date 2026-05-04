"""Schemas for runtime adapter context/result contracts."""

from pydantic import BaseModel, Field


class RuntimePlanContext(BaseModel):
    """Minimal context passed to runtime adapter in BE-03."""

    project_slug: str
    repo_path: str
    memory_path: str
    agent_slug: str
    agent_role: str
    raw_text: str
    normalized_text: str
    correlation_id: str
    idempotency_key: str
    memory_chunks: list[str] = Field(default_factory=list)


class RuntimePlanResult(BaseModel):
    """Result returned by runtime adapter for plan-only mode."""

    plan_text: str
    mode: str = "plan_only"
    session_id: str | None = None


class OpenCodeSessionMessageRequest(BaseModel):
    """Contract-aligned payload for POST /session/{id}/message.

    BE-07: keep only confirmed request field(s) for sync message endpoint.
    """

    message: str
