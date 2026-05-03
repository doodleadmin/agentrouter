"""Deprecated compatibility shim.

Use `app.policy.runtime_guardrails` directly.
"""

from app.policy.runtime_guardrails import (  # noqa: F401
    ensure_path_confined,
    is_allowed_plan_action,
    redact_payload,
    redact_text,
)
