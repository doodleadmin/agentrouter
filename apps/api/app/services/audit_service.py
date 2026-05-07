"""Security audit service — append-only trail with redaction helpers.

Never updates or deletes records. Best-effort recording available.
"""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_audit import SecurityAuditEvent

logger = logging.getLogger(__name__)

# ── Valid decision values ────────────────────────────────────────────────────
VALID_DECISIONS = frozenset({"allowed", "denied", "error"})

# ── Redaction patterns ───────────────────────────────────────────────────────
#
# These patterns are applied to free-text fields (reason) to strip
# known secret-like content before persisting to the audit table.

_REDACTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Telegram bot token: 9-10 digits:35 alphanumeric chars
    (re.compile(r"\b\d{9,10}:[A-Za-z0-9_-]{35}\b"), "[BOT_TOKEN]"),
    # Bearer auth header
    (re.compile(r"Bearer\s+\S+", re.IGNORECASE), "Bearer [REDACTED]"),
    # Common secret assignment patterns
    (
        re.compile(
            r'(password|passwd|token|secret|key)\s*[:=]\s*["\']?\S+["\']?',
            re.IGNORECASE,
        ),
        r"\1=[REDACTED]",
    ),
    # JWT / base64-encoded tokens (eyJ...)
    (re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]+"), "[JWT]"),
    # API key patterns (sk-..., pk-..., etc.)
    (re.compile(r"\b(sk|pk|api_key)[-_][A-Za-z0-9]{20,}\b"), r"\1-[REDACTED]"),
]

# Keys to strip from metadata before persisting
_FORBIDDEN_METADATA_KEYS: frozenset[str] = frozenset({
    "raw_callback_data",
    "raw_body",
    "raw_request",
    "authorization",
    "token",
    "api_key",
    "secret",
})


# ── Redaction helpers ────────────────────────────────────────────────────────


def redact_text(value: str | None, extra_patterns: list[str] | None = None) -> str | None:
    """Remove known secret-like content from reason text.

    Returns cleaned text or ``None``.
    """
    if value is None:
        return None
    for pattern, replacement in _REDACTION_PATTERNS:
        value = pattern.sub(replacement, value)
    if extra_patterns:
        for extra_re in extra_patterns:
            try:
                value = re.sub(extra_re, "[REDACTED]", value)
            except re.error:
                pass
    return value


def sanitize_metadata(metadata: dict) -> dict:
    """Strip raw callback_data, full request body, raw endpoints, and secrets."""
    if not metadata:
        return {}
    return {
        k: v
        for k, v in metadata.items()
        if k not in _FORBIDDEN_METADATA_KEYS
    }


def hash_ip(ip: str | None) -> str | None:
    """Return SHA-256 hex digest of *ip*, or ``None``."""
    if not ip:
        return None
    return hashlib.sha256(ip.encode()).hexdigest()[:32]


# ── Service ──────────────────────────────────────────────────────────────────


class SecurityAuditService:
    """Append-only security audit trail.

    Never updates or deletes records. Best-effort recording available
    via :meth:`record_best_effort`.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Write methods ────────────────────────────────────────────────────

    async def record(self, event: SecurityAuditEvent) -> SecurityAuditEvent:
        """Write one audit event. Raises on validation or DB error."""
        self._validate(event)
        self._session.add(event)
        await self._session.flush()
        return event

    @staticmethod
    async def record_best_effort(
        session: AsyncSession,
        event: SecurityAuditEvent,
        logger_override: logging.Logger | None = None,
    ) -> SecurityAuditEvent | None:
        """Write audit event without blocking primary flow.

        Returns ``None`` on failure, logs a warning.
        """
        log = logger_override or logger
        try:
            SecurityAuditService._validate(event)
            session.add(event)
            await session.flush()
            return event
        except Exception as exc:
            log.warning("audit write failed (non-blocking): %s", exc)
            return None

    # ── Query methods ────────────────────────────────────────────────────

    async def query_by_task(
        self, task_id: UUID, limit: int = 100
    ) -> list[SecurityAuditEvent]:
        """Get audit trail for a task, newest first."""
        stmt = (
            select(SecurityAuditEvent)
            .where(SecurityAuditEvent.task_id == task_id)
            .order_by(SecurityAuditEvent.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def query_by_actor(
        self, actor_id: str, days: int = 30
    ) -> list[SecurityAuditEvent]:
        """Get all events by an actor within a time window."""
        since = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        since = since - timedelta(days=days)
        stmt = (
            select(SecurityAuditEvent)
            .where(
                SecurityAuditEvent.actor_id == actor_id,
                SecurityAuditEvent.created_at >= since,
            )
            .order_by(SecurityAuditEvent.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def query_by_decision(
        self, decision: str, limit: int = 100
    ) -> list[SecurityAuditEvent]:
        """Get events by decision value (allowed / denied / error)."""
        stmt = (
            select(SecurityAuditEvent)
            .where(SecurityAuditEvent.decision == decision)
            .order_by(SecurityAuditEvent.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── Validation ───────────────────────────────────────────────────────

    @staticmethod
    def _validate(event: SecurityAuditEvent) -> None:
        """Validate required fields and decision value before persisting."""
        if event.decision not in VALID_DECISIONS:
            raise ValueError(
                f"Invalid decision: {event.decision!r} (expected one of {sorted(VALID_DECISIONS)})"
            )
        if not event.event_type:
            raise ValueError("event_type is required")
        if not event.actor_type:
            raise ValueError("actor_type is required")
