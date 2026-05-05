"""Logging redaction filter — strips secrets/tokens from log output.

TG-04 Phase 1: prevents accidental leakage of TELEGRAM_BOT_TOKEN,
CALLBACK_SECRET, API keys, and DB/Redis passwords in logs.
"""

from __future__ import annotations

import logging
import re

# ── compiled patterns ──────────────────────────────────────────────────

_BOT_TOKEN_RE = re.compile(r"\d{8,10}:[\w\-]{30,}")
_OPENAI_KEY_RE = re.compile(r"sk-[A-Za-z0-9\-_]{32,}")
_HEADER_AUTH_RE = re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*")
_DB_PASSWORD_RE = re.compile(r"(DATABASE_URL\s*=\s*)?(postgresql://[^:]+:)([^@]+)(@)")
_REDIS_PASSWORD_RE = re.compile(r"(REDIS_URL\s*=\s*)?(redis://)(:[^@]+@|default:[^@]+@)")

_REDACTION_MAP: list[tuple[re.Pattern[str], str]] = [
    (_BOT_TOKEN_RE, "***BOT_TOKEN***"),
    (_OPENAI_KEY_RE, "***OPENAI_KEY***"),
    (_HEADER_AUTH_RE, "Bearer ***REDACTED***"),
    (_DB_PASSWORD_RE, r"\2***REDACTED***\4"),
    (_REDIS_PASSWORD_RE, r"\2***REDACTED***"),
]


class SecretRedactionFilter(logging.Filter):
    """logging.Filter that strips known secret patterns from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, replacement in _REDACTION_MAP:
                record.msg = pattern.sub(replacement, record.msg)
        if record.args and isinstance(record.args, dict):
            # Redact known keys in structured kwargs
            safe = {}
            for key, value in record.args.items():
                if _is_secret_key(key):
                    safe[key] = "***REDACTED***"
                elif isinstance(value, str):
                    v = value
                    for pattern, replacement in _REDACTION_MAP:
                        v = pattern.sub(replacement, v)
                    safe[key] = v
                else:
                    safe[key] = value
            record.args = safe
        return True


def _is_secret_key(key: str) -> bool:
    lower = key.lower()
    return any(
        needle in lower
        for needle in (
            "token", "secret", "password", "api_key", "apikey",
            "authorization", "credential",
        )
    )


def install_redaction_filter(logger_name: str = "") -> None:
    """Attach SecretRedactionFilter to a specific or root logger."""
    target = logging.getLogger(logger_name)
    # Avoid duplicate attachment
    for existing in target.filters:
        if isinstance(existing, SecretRedactionFilter):
            return
    target.addFilter(SecretRedactionFilter())
