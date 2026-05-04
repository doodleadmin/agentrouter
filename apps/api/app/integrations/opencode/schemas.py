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


# ── OpenCode 1.14.33 actual contract (proven via probe) ────────────────
# POST /session/{id}/message
# Request:  {"parts": [{"type": "text", "text": "prompt"}]}
# Response: {"info": {...}, "parts": [{"type":"step-start",...},
#             {"type":"reasoning","text":"..."}, {"type":"text","text":"## Plan..."},
#             {"type":"step-finish","reason":"stop"}]}


class OpenCodeSessionTextPart(BaseModel):
    """A single text part for POST /session/{id}/message request body."""

    type: str = "text"
    text: str


class OpenCodeSessionMessageRequest(BaseModel):
    """Contract-aligned payload for POST /session/{id}/message.

    BE-07: send only parts[type=text, text=<prompt>].
    Do NOT include: message, mode, correlation_id, idempotency_key,
    restrictions, capabilities, or similar unconfirmed fields.
    """

    parts: list[OpenCodeSessionTextPart]
