"""Runtime guardrails policy (provider-agnostic)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

ALLOWED_PLAN_ACTIONS = {"read", "search", "analyze", "plan"}

_KV_SECRET_RE = re.compile(
    r"(?i)\b(api[_-]?key|token|password|secret|authorization)\b\s*[:=]\s*([^\s,;]+)"
)
_BEARER_RE = re.compile(r"(?i)\bbearer\s+([a-z0-9\-._~+/]+=*)")
_PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
    re.MULTILINE,
)
_ENV_ASSIGN_RE = re.compile(r"(?i)\b([A-Z0-9_]*(TOKEN|SECRET|PASSWORD|API_KEY)[A-Z0-9_]*)\s*=\s*([^\s]+)")


def redact_text(value: str) -> str:
    redacted = value
    redacted = _PRIVATE_KEY_RE.sub("[REDACTED_PRIVATE_KEY]", redacted)
    redacted = _BEARER_RE.sub("Bearer [REDACTED]", redacted)
    redacted = _KV_SECRET_RE.sub(lambda m: f"{m.group(1)}=[REDACTED]", redacted)
    redacted = _ENV_ASSIGN_RE.sub(lambda m: f"{m.group(1)}=[REDACTED]", redacted)
    redacted = redacted.replace(".env", "[REDACTED_PATH]")
    return redacted


def _is_sensitive_key(key: str) -> bool:
    k = key.lower()
    return any(x in k for x in ("token", "secret", "password", "api_key", "authorization", "private_key"))


def redact_payload(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_payload(v) for v in value]
    if isinstance(value, dict):
        safe: dict[str, Any] = {}
        for k, v in value.items():
            safe[k] = "[REDACTED]" if _is_sensitive_key(k) else redact_payload(v)
        return safe
    return value


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
