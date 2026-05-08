"""Centralized secrets redaction module (SEC-03 Phase 2).

Single source of truth for redacting secrets from strings, dicts, lists,
and structured payloads. All instrumented code paths MUST import from here.

Patterns are applied in order; earlier patterns take priority over later ones
when they overlap. All replacements are deterministic (same input → same output).
"""

from __future__ import annotations

import re
from typing import Any

# ── Compiled redaction patterns (order matters) ──────────────────────────────

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # 1. Telegram bot token: 8-11 digits : 30-45 alphanumeric chars
    (re.compile(r"\b\d{8,11}:[\w\-]{30,45}\b"), "[REDACTED:TELEGRAM_TOKEN]"),
    # 2. Bearer token (case-insensitive header + opaque/charset token)
    (
        re.compile(r"(?i)Bearer\s+[A-Za-z0-9\-._~+/]+={0,2}"),
        "Bearer [REDACTED:BEARER_TOKEN]",
    ),
    # 3. JWT (eyJ… header.payload.signature)
    (
        re.compile(r"\beyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\b"),
        "[REDACTED:JWT]",
    ),
    # 4. API key sk-(ant-)… (OpenAI, Anthropic, etc.)
    (
        re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9\-]{20,}\b"),
        "[REDACTED:API_KEY]",
    ),
    # 5. GitHub tokens (classic + fine-grained PAT)
    (
        re.compile(
            r"\b(?:gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{20,})\b"
        ),
        "[REDACTED:GITHUB_TOKEN]",
    ),
    # 6. DB URLs with embedded password (postgres, mysql, mongodb)
    (
        re.compile(
            r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?)://[^:@\s]+:[^@\s]+@"
        ),
        "[REDACTED:DB_PASSWORD]",
    ),
    # 7. Redis URLs with embedded password
    (
        re.compile(r"\bredis://(?:[^:@\s]*):[^@\s]+@"),
        "[REDACTED:REDIS_PASSWORD]",
    ),
    # 8. Generic key=value / key:value assignments (keep key name)
    (
        re.compile(
            r"(?i)\b(password|secret|token|api_key|apikey|access_key|private_key)\s*[=:]\s*[^\s,\n;]+"
        ),
        r"\1=[REDACTED:SECRET]",
    ),
    # 9. PEM private key blocks (RSA/EC/DSA/OPENSSH)
    (
        re.compile(
            r"-----BEGIN\s+(?:RSA|EC|DSA|OPENSSH)?\s*PRIVATE KEY-----[\s\S]*?"
            r"-----END\s+(?:RSA|EC|DSA|OPENSSH)?\s*PRIVATE KEY-----",
            re.IGNORECASE,
        ),
        "[REDACTED:PRIVATE_KEY]",
    ),
    # 10. CALLBACK_SECRET env var assignment
    (
        re.compile(r"CALLBACK_SECRET\s*=\s*\S+"),
        "[REDACTED:CALLBACK_SECRET]",
    ),
]

# ── Sensitive key detection (for redact_mapping key-level redaction) ────────

_SENSITIVE_KEY_TOKENS = (
    "token",
    "secret",
    "password",
    "api_key",
    "apikey",
    "authorization",
    "private_key",
    "access_key",
    "bearer",
)

_FORBIDDEN_METADATA_KEYS: frozenset[str] = frozenset({
    "raw_callback_data",
    "raw_body",
    "raw_request",
    "authorization",
    "token",
    "api_key",
    "secret",
    "password",
    "private_key",
    "access_key",
    "bearer",
})


def _is_sensitive_key(key: str) -> bool:
    """Check if a dict key refers to a sensitive/secret field."""
    k = key.lower()
    return any(tok in k for tok in _SENSITIVE_KEY_TOKENS)


# ── Public API ───────────────────────────────────────────────────────────────


def redact_text(value: object) -> object:
    """Redact secrets in a string. Non-strings pass through unchanged. Never throws.

    Returns the same type that was passed in, with secrets replaced by
    deterministic ``[REDACTED:<TYPE>]`` markers.
    """
    if not isinstance(value, str):
        return value
    result = value
    for pattern, replacement in _PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def redact_mapping(data: dict | list | str | None) -> dict | list | str | None:
    """Recursively redact all string values in nested dict/list structures.

    - Dict keys that look sensitive have their *values* replaced with
      ``[REDACTED:SECRET]`` (the key is preserved for structure).
    - Strings are passed through :func:`redact_text`.
    - Non-string leaf values are returned unchanged.
    """
    if isinstance(data, dict):
        result: dict[str, Any] = {}
        for key, value in data.items():
            if _is_sensitive_key(key):
                result[key] = "[REDACTED:SECRET]"
            else:
                result[key] = redact_mapping(value)  # type: ignore[assignment]
        return result
    if isinstance(data, list):
        return [redact_mapping(item) for item in data]  # type: ignore[return-value]
    if isinstance(data, str):
        return redact_text(data)  # type: ignore[return-value]
    return data


def contains_secret(text: object) -> bool:
    """Return ``True`` if any known secret pattern is found in *text*.

    Never exposes the raw value — only the detection result.
    """
    if not isinstance(text, str):
        return False
    for pattern, _ in _PATTERNS:
        if pattern.search(text):
            return True
    return False


def sanitize_metadata(metadata: dict | None) -> dict:
    """Remove sensitive keys from a metadata dict. Handles ``None`` safely.

    Strips keys listed in ``_FORBIDDEN_METADATA_KEYS``, leaving
    non-sensitive entries untouched.
    """
    if metadata is None:
        return {}
    return {
        key: value
        for key, value in metadata.items()
        if key not in _FORBIDDEN_METADATA_KEYS
    }


def find_secret_matches(text: object) -> list[str]:
    """Return list of detected secret *types* (e.g. ``['TELEGRAM_TOKEN', 'JWT']``).

    Never returns raw secret values. Returns empty list for non-strings.
    """
    if not isinstance(text, str):
        return []
    found: list[str] = []
    _type_re = re.compile(r"\[REDACTED:([A-Z_]+)\]")
    redacted = text
    for pattern, replacement in _PATTERNS:
        new_text = pattern.sub(replacement, redacted)
        if new_text != redacted:
            # Extract type from replacement marker
            match = _type_re.search(replacement)
            if match:
                type_label = match.group(1)
                if type_label not in found:
                    found.append(type_label)
        redacted = new_text
    return found
