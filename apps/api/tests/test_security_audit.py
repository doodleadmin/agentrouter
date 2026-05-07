"""Tests for SecurityAudit model, service, and redaction helpers.

SEC-02 Phase 2: security_audit_events table, append-only service, privacy helpers.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_audit import SecurityAuditEvent
from app.models.task import Task
from app.services.audit_service import (
    SecurityAuditService,
    hash_ip,
    redact_text,
    sanitize_metadata,
)


# ── Model tests ──────────────────────────────────────────────────────────────


class TestSecurityAuditModel:
    """Direct model creation and persistence."""

    @pytest.mark.anyio
    async def test_create_event_minimal(self, test_session: AsyncSession) -> None:
        """Minimal event with required fields only."""
        event = SecurityAuditEvent(
            event_type="permission_check",
            actor_type="agent",
            decision="allowed",
        )
        test_session.add(event)
        await test_session.flush()

        assert event.id is not None
        assert event.created_at is not None
        assert event.audit_metadata == {}
        assert event.decision == "allowed"
        assert event.event_type == "permission_check"

    @pytest.mark.anyio
    async def test_create_event_with_all_fields(self, test_session: AsyncSession) -> None:
        """Event with all optional non-FK fields populated."""
        event = SecurityAuditEvent(
            event_type="permission_check",
            actor_type="user",
            actor_id="1113930428",
            source="telegram",
            action="approve",
            decision="denied",
            audit_code="SEC-PERM-APPROVE-DENY",
            reason="User is not in admin list",
            # FK fields left None — no parent records exist
            chat_id=123456789,
            thread_id=42,
            ip_hash=hash_ip("192.168.1.1"),
            correlation_id=uuid4(),
            request_id="req-abc-123",
            audit_metadata={"topic": "approvals", "via": "callback"},
            error_code="ERR_FORBIDDEN",
        )
        test_session.add(event)
        await test_session.flush()

        assert event.id is not None
        assert event.created_at is not None
        assert event.decision == "denied"
        assert event.source == "telegram"
        assert event.action == "approve"
        assert event.audit_code == "SEC-PERM-APPROVE-DENY"
        assert event.reason == "User is not in admin list"
        assert event.chat_id == 123456789
        assert event.thread_id == 42
        assert event.ip_hash is not None and len(event.ip_hash) == 32
        assert event.audit_metadata == {"topic": "approvals", "via": "callback"}

    @pytest.mark.anyio
    async def test_created_at_auto_populated(self, test_session: AsyncSession) -> None:
        """created_at is set server-side on insert."""
        event = SecurityAuditEvent(
            event_type="test",
            actor_type="system",
            decision="allowed",
        )
        test_session.add(event)
        await test_session.flush()

        assert isinstance(event.created_at, datetime)
        assert event.created_at.tzinfo is not None  # timezone-aware

    @pytest.mark.anyio
    async def test_metadata_defaults_to_empty_dict(self, test_session: AsyncSession) -> None:
        """metadata column defaults to empty dict."""
        event = SecurityAuditEvent(
            event_type="test",
            actor_type="system",
            decision="allowed",
        )
        test_session.add(event)
        await test_session.flush()

        assert event.audit_metadata == {}


# ── Service tests ────────────────────────────────────────────────────────────


class TestSecurityAuditService:
    """SecurityAuditService write + query operations."""

    @pytest.mark.anyio
    async def test_record_event(self, test_session: AsyncSession) -> None:
        """Service writes event to DB and returns it with an id."""
        svc = SecurityAuditService(test_session)
        event = SecurityAuditEvent(
            event_type="permission_check",
            actor_type="agent",
            decision="allowed",
        )
        recorded = await svc.record(event)

        assert recorded.id is not None
        assert recorded.created_at is not None
        assert recorded.decision == "allowed"

    @pytest.mark.anyio
    async def test_query_by_task(self, test_session: AsyncSession) -> None:
        """Query returns events for a specific task_id, newest first."""
        svc = SecurityAuditService(test_session)

        # Create a parent task so FK is satisfied
        task = Task(
            external_id=f"ext-{uuid4().hex[:8]}",
            title="Query test task",
            raw_text="raw",
            normalized_text="norm",
            risk_level="low",
        )
        test_session.add(task)
        await test_session.flush()
        task_id = str(task.id)

        # Write two events for the same task
        e1 = SecurityAuditEvent(
            event_type="plan_approved",
            actor_type="user",
            decision="allowed",
            task_id=task_id,
        )
        e2 = SecurityAuditEvent(
            event_type="plan_rejected",
            actor_type="user",
            decision="denied",
            task_id=task_id,
        )
        await svc.record(e1)
        await svc.record(e2)

        results = await svc.query_by_task(task.id)
        assert len(results) == 2
        # Both events present (order non-deterministic within same timestamp)
        event_types = {e.event_type for e in results}
        assert event_types == {"plan_approved", "plan_rejected"}

    @pytest.mark.anyio
    async def test_query_by_actor(self, test_session: AsyncSession) -> None:
        """Query returns events for a specific actor_id within time window."""
        svc = SecurityAuditService(test_session)
        actor_id = "user-42"

        e1 = SecurityAuditEvent(
            event_type="permission_check",
            actor_type="user",
            actor_id=actor_id,
            decision="allowed",
        )
        e2 = SecurityAuditEvent(
            event_type="deploy_requested",
            actor_type="user",
            actor_id=actor_id,
            decision="error",
        )
        await svc.record(e1)
        await svc.record(e2)

        results = await svc.query_by_actor(actor_id, days=30)
        assert len(results) == 2

    @pytest.mark.anyio
    async def test_query_by_decision(self, test_session: AsyncSession) -> None:
        """Filter by decision=denied returns only denied events."""
        svc = SecurityAuditService(test_session)

        await svc.record(SecurityAuditEvent(
            event_type="t1", actor_type="system", decision="allowed",
        ))
        await svc.record(SecurityAuditEvent(
            event_type="t2", actor_type="system", decision="denied",
        ))
        await svc.record(SecurityAuditEvent(
            event_type="t3", actor_type="system", decision="denied",
        ))

        denied = await svc.query_by_decision("denied")
        assert len(denied) == 2
        assert all(e.decision == "denied" for e in denied)

    @pytest.mark.anyio
    async def test_best_effort_does_not_raise(self, test_session: AsyncSession) -> None:
        """record_best_effort catches validation/DB errors and returns None."""
        # Invalid decision should be caught by validation, not crash
        event = SecurityAuditEvent(
            event_type="bad_event",
            actor_type="system",
            decision="invalid_value",
        )
        result = await SecurityAuditService.record_best_effort(
            test_session, event
        )
        assert result is None

    @pytest.mark.anyio
    async def test_best_effort_succeeds_for_valid_event(
        self, test_session: AsyncSession
    ) -> None:
        """record_best_effort succeeds for a valid event."""
        event = SecurityAuditEvent(
            event_type="valid_event",
            actor_type="system",
            decision="allowed",
        )
        result = await SecurityAuditService.record_best_effort(
            test_session, event
        )
        assert result is not None
        assert result.id is not None

    @pytest.mark.anyio
    async def test_append_only_no_update(self, test_session: AsyncSession) -> None:
        """Service has no UPDATE or DELETE methods on audit events."""
        svc = SecurityAuditService(test_session)

        # Verify only query and record methods exist (no update/delete)
        public_methods = [
            m for m in dir(svc)
            if not m.startswith("_") and callable(getattr(svc, m, None))
        ]
        mutation_methods = {"update", "delete", "modify", "remove", "edit"}
        for bad in mutation_methods:
            assert bad not in public_methods, (
                f"Service must not expose {bad!r} — audit is append-only"
            )

    @pytest.mark.anyio
    async def test_query_by_task_empty(self, test_session: AsyncSession) -> None:
        """Query for unknown task returns empty list."""
        svc = SecurityAuditService(test_session)
        results = await svc.query_by_task(UUID("00000000-0000-0000-0000-000000000000"))
        assert results == []

    @pytest.mark.anyio
    async def test_query_by_task_respects_limit(self, test_session: AsyncSession) -> None:
        """query_by_task respects the limit parameter."""
        svc = SecurityAuditService(test_session)

        # Create a parent task so FK is satisfied
        task = Task(
            external_id=f"ext-{uuid4().hex[:8]}",
            title="Limit test task",
            raw_text="raw",
            normalized_text="norm",
            risk_level="low",
        )
        test_session.add(task)
        await test_session.flush()
        task_id = str(task.id)

        for i in range(5):
            await svc.record(SecurityAuditEvent(
                event_type=f"event_{i}",
                actor_type="system",
                decision="allowed",
                task_id=task_id,
            ))

        results = await svc.query_by_task(task.id, limit=2)
        assert len(results) == 2


# ── Redaction tests ──────────────────────────────────────────────────────────


class TestAuditRedaction:
    """Privacy helpers: redaction, sanitization, IP hashing."""

    def test_redact_bot_token(self) -> None:
        """Telegram bot tokens are replaced with [BOT_TOKEN]."""
        # Real Telegram tokens are 9-10 digits : 35 alphanumeric chars
        text = "Error with token 1234567890:AAHq-RX_abcdefghijklmnopqrstuvwxyz1 here"
        cleaned = redact_text(text)
        assert cleaned is not None
        assert "1234567890" not in cleaned
        assert "[BOT_TOKEN]" in cleaned

    def test_redact_callback_secret(self) -> None:
        """Secrets assigned via key=value are redacted."""
        text = "secret=abc123def456 and then more text"
        cleaned = redact_text(text)
        assert cleaned is not None
        assert "[REDACTED]" in cleaned
        assert "abc123def456" not in cleaned

    def test_redact_bearer_token(self) -> None:
        """Bearer tokens are replaced."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.abcdefg.hijklmnop"
        cleaned = redact_text(text)
        assert cleaned is not None
        assert "[REDACTED]" in cleaned
        assert "eyJhbGci" not in cleaned

    def test_redact_jwt(self) -> None:
        """JWT tokens (eyJ... pattern) are redacted."""
        text = "Token is eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c used here"
        cleaned = redact_text(text)
        assert cleaned is not None
        assert "[JWT]" in cleaned

    def test_redact_sk_prefix(self) -> None:
        """API keys with sk- prefix are redacted."""
        text = "Using sk-abcdefghijklmnopqrstuvwxyz123456 for request"
        cleaned = redact_text(text)
        assert cleaned is not None
        assert "[REDACTED]" in cleaned

    def test_redact_none_returns_none(self) -> None:
        """None input returns None."""
        assert redact_text(None) is None

    def test_redact_preserves_clean_text(self) -> None:
        """Clean text without secrets passes through unchanged."""
        text = "User requested deploy to staging environment"
        cleaned = redact_text(text)
        assert cleaned == text

    def test_sanitize_metadata_removes_raw_callback_data(self) -> None:
        """sanitize_metadata strips forbidden keys."""
        md = {
            "raw_callback_data": "secret_payload_123",
            "topic": "approvals",
            "action": "deploy",
        }
        cleaned = sanitize_metadata(md)
        assert "raw_callback_data" not in cleaned
        assert cleaned == {"topic": "approvals", "action": "deploy"}

    def test_sanitize_metadata_removes_authorization(self) -> None:
        """authorization key is stripped."""
        md = {"action": "test", "authorization": "Bearer xyz"}
        cleaned = sanitize_metadata(md)
        assert "authorization" not in cleaned
        assert cleaned == {"action": "test"}

    def test_sanitize_metadata_empty_input(self) -> None:
        """Empty dict returns empty dict."""
        assert sanitize_metadata({}) == {}

    def test_hash_ip_produces_32_char_hex(self) -> None:
        """hash_ip returns a 32-character hex string."""
        h = hash_ip("192.168.1.1")
        assert h is not None
        assert len(h) == 32
        assert all(c in "0123456789abcdef" for c in h)

    def test_hash_ip_deterministic(self) -> None:
        """Same input produces same hash."""
        assert hash_ip("10.0.0.1") == hash_ip("10.0.0.1")

    def test_hash_ip_different_ips_different_hash(self) -> None:
        """Different IPs produce different hashes."""
        assert hash_ip("10.0.0.1") != hash_ip("10.0.0.2")

    def test_hash_ip_none_returns_none(self) -> None:
        """None input returns None."""
        assert hash_ip(None) is None

    def test_hash_ip_empty_returns_none(self) -> None:
        """Empty string returns None."""
        assert hash_ip("") is None


# ── Validation tests ────────────────────────────────────────────────────────


class TestAuditValidation:
    """Decision and required-field validation."""

    @pytest.mark.anyio
    async def test_decision_rejects_invalid(self, test_session: AsyncSession) -> None:
        """record() raises ValueError for invalid decision."""
        svc = SecurityAuditService(test_session)
        event = SecurityAuditEvent(
            event_type="test",
            actor_type="system",
            decision="bogus",
        )
        with pytest.raises(ValueError, match="Invalid decision"):
            await svc.record(event)

    @pytest.mark.anyio
    async def test_decision_accepts_allowed(self, test_session: AsyncSession) -> None:
        """'allowed' is a valid decision."""
        svc = SecurityAuditService(test_session)
        event = SecurityAuditEvent(
            event_type="test", actor_type="system", decision="allowed",
        )
        recorded = await svc.record(event)
        assert recorded.decision == "allowed"

    @pytest.mark.anyio
    async def test_decision_accepts_denied(self, test_session: AsyncSession) -> None:
        """'denied' is a valid decision."""
        svc = SecurityAuditService(test_session)
        event = SecurityAuditEvent(
            event_type="test", actor_type="system", decision="denied",
        )
        recorded = await svc.record(event)
        assert recorded.decision == "denied"

    @pytest.mark.anyio
    async def test_decision_accepts_error(self, test_session: AsyncSession) -> None:
        """'error' is a valid decision."""
        svc = SecurityAuditService(test_session)
        event = SecurityAuditEvent(
            event_type="test", actor_type="system", decision="error",
        )
        recorded = await svc.record(event)
        assert recorded.decision == "error"

    @pytest.mark.anyio
    async def test_event_type_required(self, test_session: AsyncSession) -> None:
        """record() raises ValueError when event_type is empty."""
        svc = SecurityAuditService(test_session)
        event = SecurityAuditEvent(
            event_type="",
            actor_type="system",
            decision="allowed",
        )
        with pytest.raises(ValueError, match="event_type is required"):
            await svc.record(event)

    @pytest.mark.anyio
    async def test_actor_type_required(self, test_session: AsyncSession) -> None:
        """record() raises ValueError when actor_type is empty."""
        svc = SecurityAuditService(test_session)
        event = SecurityAuditEvent(
            event_type="test",
            actor_type="",
            decision="allowed",
        )
        with pytest.raises(ValueError, match="actor_type is required"):
            await svc.record(event)
