"""Runtime guardrails policy (provider-agnostic).

SEC-03 Phase 2: redaction functions delegate to centralized module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.security.redaction import redact_mapping, redact_text  # centralized (SEC-03)  # noqa: F401

ALLOWED_PLAN_ACTIONS = {"read", "search", "analyze", "plan"}


def redact_payload(value: Any) -> Any:
    """Recursively redact secrets in payload — delegates to centralized redact_mapping."""
    return redact_mapping(value)


def ensure_path_confined(path_value: str, allowed_root: str) -> str:
    p = Path(path_value)
    root = Path(allowed_root)

    if str(path_value).startswith("\\\\"):
        raise ValueError("UNC/network paths are forbidden")
    if p.is_absolute() and root.drive and p.drive.lower() != root.drive.lower():
        raise ValueError("Path drive mismatch")

    resolved_root = root.resolve()
    candidate = (resolved_root / p).resolve() if not p.is_absolute() else p.resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("Path escapes allowed root") from exc
    return str(candidate)


def is_allowed_plan_action(action: str) -> bool:
    return action in ALLOWED_PLAN_ACTIONS
