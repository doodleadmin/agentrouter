"""Schemas for runtime adapter context/result contracts."""

from pydantic import BaseModel


class RuntimePlanContext(BaseModel):
    """Minimal context passed to runtime adapter in BE-03."""

    project_slug: str
    repo_path: str
    memory_path: str
    agent_slug: str
    agent_role: str
    raw_text: str
    normalized_text: str


class RuntimePlanResult(BaseModel):
    """Result returned by runtime adapter for plan-only mode."""

    plan_text: str
    mode: str = "plan_only"
