"""Log/output redaction for WRK-03 execution pipeline.

Keep in sync with apps/api/app/security/redaction.py; SEC-03 Phase 2.
If cross-app import becomes viable, prefer importing from the API module.
"""

from __future__ import annotations

import re

# ── Redaction patterns — order matters (same as API module) ──────────────────

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # 1. Telegram bot token
    (re.compile(r"\b\d{8,11}:[\w\-]{30,45}\b"), "[REDACTED:TELEGRAM_TOKEN]"),
    # 2. Bearer token
    (
        re.compile(r"(?i)Bearer\s+[A-Za-z0-9\-._~+/]+={0,2}"),
        "Bearer [REDACTED:BEARER_TOKEN]",
    ),
    # 3. JWT
    (
        re.compile(r"\beyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\b"),
        "[REDACTED:JWT]",
    ),
    # 4. API key sk-*
    (
        re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9\-]{20,}\b"),
        "[REDACTED:API_KEY]",
    ),
    # 5. GitHub tokens
    (
        re.compile(
            r"\b(?:gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{20,})\b"
        ),
        "[REDACTED:GITHUB_TOKEN]",
    ),
    # 6. DB URLs with password
    (
        re.compile(
            r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?)://[^:@\s]+:[^@\s]+@"
        ),
        "[REDACTED:DB_PASSWORD]",
    ),
    # 7. Redis URLs with password
    (
        re.compile(r"\bredis://(?:[^:@\s]*):[^@\s]+@"),
        "[REDACTED:REDIS_PASSWORD]",
    ),
    # 8. Generic key=value assignments
    (
        re.compile(
            r"(?i)\b(password|secret|token|api_key|apikey|access_key|private_key)\s*[=:]\s*[^\s,\n;]+"
        ),
        r"\1=[REDACTED:SECRET]",
    ),
    # 9. PEM private key blocks
    (
        re.compile(
            r"-----BEGIN\s+(?:RSA|EC|DSA|OPENSSH)?\s*PRIVATE KEY-----[\s\S]*?"
            r"-----END\s+(?:RSA|EC|DSA|OPENSSH)?\s*PRIVATE KEY-----",
            re.IGNORECASE,
        ),
        "[REDACTED:PRIVATE_KEY]",
    ),
    # 10. CALLBACK_SECRET env var
    (
        re.compile(r"CALLBACK_SECRET\s*=\s*\S+"),
        "[REDACTED:CALLBACK_SECRET]",
    ),
]


def redact_text(text: str, *, max_len: int = 10_000) -> str:
    """Redact secrets and truncate long output.

    Uses the same 10-pattern set as ``apps.api.app.security.redaction``.
    """
    redacted: str = text
    for pattern, replacement in _PATTERNS:
        redacted = pattern.sub(replacement, redacted)

    if len(redacted) > max_len:
        return redacted[:max_len] + "\n...[TRUNCATED]"
    return redacted
