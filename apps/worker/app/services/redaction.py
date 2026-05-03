"""Log/output redaction for WRK-03 execution pipeline."""

from __future__ import annotations

import re

_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(password\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(token\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)([^\s,;]+)"),
    re.compile(r"(?i)(bearer\s+)([^\s,;]+)"),
    re.compile(r"(?i)(postgres(?:ql)?://)([^\s]+)"),
    re.compile(r"(?i)(mysql://)([^\s]+)"),
    re.compile(r"(?i)(mongodb(?:\+srv)?://)([^\s]+)"),
)

_PRIVATE_KEY_BLOCK = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
    re.IGNORECASE,
)


def redact_text(text: str, *, max_len: int = 10_000) -> str:
    """Redact secrets and truncate long output."""
    redacted = text

    redacted = _PRIVATE_KEY_BLOCK.sub("[REDACTED_PRIVATE_KEY_BLOCK]", redacted)
    for pattern in _PATTERNS:
        redacted = pattern.sub(r"\1[REDACTED]", redacted)

    if len(redacted) > max_len:
        return redacted[:max_len] + "\n...[TRUNCATED]"
    return redacted
