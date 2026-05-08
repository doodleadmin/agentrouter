"""Tests for centralized secrets redaction module (SEC-03 Phase 2).

Covers all 10 pattern types, recursive mapping, edge cases, and
integration guardrails.
"""

from __future__ import annotations

import pytest

from app.security.redaction import (
    contains_secret,
    find_secret_matches,
    redact_mapping,
    redact_text,
    sanitize_metadata,
)

# Ensure models are registered with Base.metadata before test_session creates tables
import app.models  # noqa: F401


# ── Synthetic test secrets (FAKE — no real credentials) ─────────────────────

FAKE_TELEGRAM_TOKEN = "1234567890:AAHq-RX_abcdefghijklmnopqrstuvwxyz1"
FAKE_BEARER = "Bearer eyJhbGciOiJIUzI1NiJ9.dGVzdC50b2tlbg"
FAKE_JWT = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
    "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
)
FAKE_SK_KEY = "sk-ant-api03-abcdefghijklmnopqrstuvwxyz"
FAKE_GH_TOKEN = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"
FAKE_GH_PAT = "github_pat_11ABCDEFGHIJKLMNOPQRSTUVWXYZ"
FAKE_DB_URL = "postgresql://user:secret123@localhost:5432/db"
FAKE_REDIS_URL = "redis://:mypassword@localhost:6379/0"


# ── redact_text tests ────────────────────────────────────────────────────────


class TestRedactText:
    """Unit tests for redact_text covering all pattern types."""

    def test_redact_telegram_bot_token(self) -> None:
        result = redact_text(f"Error with token {FAKE_TELEGRAM_TOKEN} here")
        assert isinstance(result, str)
        assert "[REDACTED:TELEGRAM_TOKEN]" in result
        assert FAKE_TELEGRAM_TOKEN not in result

    def test_redact_bearer_token(self) -> None:
        result = redact_text(f"Auth: {FAKE_BEARER} and more")
        assert isinstance(result, str)
        assert "[REDACTED:BEARER_TOKEN]" in result
        assert "eyJhbGci" not in result

    def test_redact_jwt(self) -> None:
        result = redact_text(f"Token is {FAKE_JWT} used here")
        assert isinstance(result, str)
        assert "[REDACTED:JWT]" in result
        assert "eyJ" not in result

    def test_redact_api_key_sk(self) -> None:
        result = redact_text(f"Using {FAKE_SK_KEY} for request")
        assert isinstance(result, str)
        assert "[REDACTED:API_KEY]" in result
        assert FAKE_SK_KEY not in result

    def test_redact_github_token(self) -> None:
        result = redact_text(f"GITHUB_TOKEN={FAKE_GH_TOKEN}")
        assert isinstance(result, str)
        assert "[REDACTED:GITHUB_TOKEN]" in result
        assert FAKE_GH_TOKEN not in result

    def test_redact_github_pat(self) -> None:
        # Use standalone token — avoid "token:" prefix which would also
        # be caught by the generic assignment pattern #8.
        result = redact_text(f"auth with {FAKE_GH_PAT} and more")
        assert isinstance(result, str)
        assert "[REDACTED:GITHUB_TOKEN]" in result
        assert FAKE_GH_PAT not in result

    def test_redact_db_url_password(self) -> None:
        result = redact_text(f"url={FAKE_DB_URL}")
        assert isinstance(result, str)
        assert "[REDACTED:DB_PASSWORD]" in result
        assert "secret123" not in result

    def test_redact_redis_url_password(self) -> None:
        result = redact_text(f"redis={FAKE_REDIS_URL}")
        assert isinstance(result, str)
        assert "[REDACTED:REDIS_PASSWORD]" in result
        assert "mypassword" not in result

    def test_redact_generic_assignment(self) -> None:
        result = redact_text("secret=abc123def456 and then more text")
        assert isinstance(result, str)
        # Generic assignment keeps the key name
        assert "secret=[REDACTED:SECRET]" in result
        assert "abc123def456" not in result

    def test_redact_pem_private_key(self) -> None:
        pem = (
            "-----BEGIN RSA PRIVATE KEY-----\n"
            "MIIEpAIBAAKCAQEA0Z3...fake...\n"
            "-----END RSA PRIVATE KEY-----"
        )
        result = redact_text(f"Key data:\n{pem}\nend")
        assert isinstance(result, str)
        assert "[REDACTED:PRIVATE_KEY]" in result
        assert "BEGIN RSA PRIVATE KEY" not in result

    def test_redact_callback_secret(self) -> None:
        result = redact_text("CALLBACK_SECRET=supersecretvalue123")
        assert isinstance(result, str)
        assert "[REDACTED:CALLBACK_SECRET]" in result
        assert "supersecretvalue123" not in result

    def test_passthrough_int(self) -> None:
        assert redact_text(42) == 42

    def test_passthrough_bool(self) -> None:
        assert redact_text(True) is True

    def test_passthrough_none(self) -> None:
        assert redact_text(None) is None

    def test_passthrough_empty_string(self) -> None:
        assert redact_text("") == ""

    def test_preserves_clean_text(self) -> None:
        text = "User requested deploy to staging environment"
        assert redact_text(text) == text

    def test_deterministic(self) -> None:
        text = f"token={FAKE_JWT} and key={FAKE_SK_KEY}"
        r1 = redact_text(text)
        r2 = redact_text(text)
        assert r1 == r2

    def test_no_raw_secret_in_output(self) -> None:
        """Redacted output must never contain raw secret values."""
        text = f"Using token {FAKE_TELEGRAM_TOKEN} for auth"
        result = redact_text(text)
        assert isinstance(result, str)
        assert FAKE_TELEGRAM_TOKEN not in result
        # Check that random slice of the original doesn't leak
        assert "1234567890:AAHq" not in result

    def test_never_throws_on_none(self) -> None:
        """redact_text must never throw on None input."""
        assert redact_text(None) is None

    def test_never_throws_on_int(self) -> None:
        """redact_text must never throw on int input."""
        assert redact_text(0) == 0


# ── redact_mapping tests ─────────────────────────────────────────────────────


class TestRedactMapping:
    """Recursive redaction of nested dict/list structures."""

    def test_flat_dict(self) -> None:
        data = {"message": f"Login with {FAKE_JWT}", "count": 5}
        result = redact_mapping(data)
        assert isinstance(result, dict)
        assert "[REDACTED:JWT]" in result["message"]
        assert result["count"] == 5

    def test_nested_dict(self) -> None:
        data = {
            "auth": {"token": FAKE_JWT, "type": "bearer"},
            "db": {"url": FAKE_DB_URL},
        }
        result = redact_mapping(data)
        # "token" is a sensitive key → value replaced entirely
        assert result["auth"]["token"] == "[REDACTED:SECRET]"
        # "url" is not a sensitive key → value content is redacted
        assert "[REDACTED:DB_PASSWORD]" in result["db"]["url"]

    def test_list_of_dicts(self) -> None:
        data = [
            {"name": "db1", "url": FAKE_DB_URL},
            {"name": "redis1", "url": FAKE_REDIS_URL},
        ]
        result = redact_mapping(data)
        assert "[REDACTED:DB_PASSWORD]" in result[0]["url"]
        assert "[REDACTED:REDIS_PASSWORD]" in result[1]["url"]

    def test_sensitive_key_redacted(self) -> None:
        """Keys like 'token', 'secret' have their values replaced."""
        data = {"token": "real-secret-12345", "api_key": "sk-live-abcdef"}
        result = redact_mapping(data)
        assert result["token"] == "[REDACTED:SECRET]"
        assert result["api_key"] == "[REDACTED:SECRET]"

    def test_non_sensitive_key_passthrough(self) -> None:
        data = {"name": "John", "age": 30}
        result = redact_mapping(data)
        assert result == {"name": "John", "age": 30}

    def test_passthrough_non_string_leaf(self) -> None:
        data = {"value": None, "count": 0, "active": False}
        result = redact_mapping(data)
        assert result == {"value": None, "count": 0, "active": False}

    def test_none_input(self) -> None:
        assert redact_mapping(None) is None


# ── contains_secret tests ────────────────────────────────────────────────────


class TestContainsSecret:
    """Detection-only function — never exposes raw values."""

    def test_detects_telegram_token(self) -> None:
        assert contains_secret(FAKE_TELEGRAM_TOKEN) is True

    def test_detects_jwt(self) -> None:
        assert contains_secret(FAKE_JWT) is True

    def test_no_secret_in_clean_text(self) -> None:
        assert contains_secret("Hello, world!") is False

    def test_no_secret_in_empty_string(self) -> None:
        assert contains_secret("") is False

    def test_no_secret_in_none(self) -> None:
        assert contains_secret(None) is False

    def test_no_secret_in_int(self) -> None:
        assert contains_secret(42) is False


# ── find_secret_matches tests ────────────────────────────────────────────────


class TestFindSecretMatches:
    """Returns list of detected secret types without raw values."""

    def test_single_match(self) -> None:
        text = f"Error with {FAKE_TELEGRAM_TOKEN}"
        matches = find_secret_matches(text)
        assert "TELEGRAM_TOKEN" in matches

    def test_multiple_matches(self) -> None:
        text = f"token={FAKE_JWT} key={FAKE_SK_KEY}"
        matches = find_secret_matches(text)
        assert "JWT" in matches
        assert "API_KEY" in matches

    def test_no_matches_clean_text(self) -> None:
        assert find_secret_matches("Clean text") == []

    def test_no_matches_none(self) -> None:
        assert find_secret_matches(None) == []

    def test_no_matches_int(self) -> None:
        assert find_secret_matches(42) == []

    def test_no_raw_values_returned(self) -> None:
        """find_secret_matches must only return type labels, never raw data."""
        text = f"secret=supersecret123 {FAKE_JWT}"
        matches = find_secret_matches(text)
        for m in matches:
            assert "supersecret" not in m
            assert "eyJ" not in m


# ── sanitize_metadata tests ──────────────────────────────────────────────────


class TestSanitizeMetadata:
    """Metadata key stripping."""

    def test_removes_sensitive_keys(self) -> None:
        md = {
            "raw_callback_data": "secret_payload_123",
            "authorization": "Bearer xyz",
            "token": "abc123",
            "api_key": "sk-test",
            "secret": "s3cr3t",
            "password": "pass123",
            "private_key": "-----BEGIN RSA...",
            "access_key": "AKIA123",
            "bearer": "tok123",
            "raw_body": '{"cmd":"delete"}',
            "raw_request": "POST /admin",
            "topic": "approvals",
            "action": "deploy",
        }
        cleaned = sanitize_metadata(md)
        assert "raw_callback_data" not in cleaned
        assert "authorization" not in cleaned
        assert "token" not in cleaned
        assert "api_key" not in cleaned
        assert "secret" not in cleaned
        assert "password" not in cleaned
        assert "private_key" not in cleaned
        assert "access_key" not in cleaned
        assert "bearer" not in cleaned
        assert "raw_body" not in cleaned
        assert "raw_request" not in cleaned
        # Non-sensitive keys preserved
        assert cleaned == {"topic": "approvals", "action": "deploy"}

    def test_empty_dict(self) -> None:
        assert sanitize_metadata({}) == {}

    def test_none_input(self) -> None:
        assert sanitize_metadata(None) == {}

    def test_all_safe_keys_preserved(self) -> None:
        md = {"project": "academy-bot", "env": "staging", "chat_id": 123}
        assert sanitize_metadata(md) == md


# ── Integration tests for task_event payload redaction ───────────────────────


@pytest.mark.anyio
class TestTaskEventPayloadRedaction:
    """Verify task event payload gets redacted before persisting."""

    @staticmethod
    async def _create_task(session, title: str = "test-redact") -> UUID:
        """Helper: create a minimal Task so FK constraints are satisfied."""
        from uuid import uuid4

        from app.models.task import Task

        task_id = uuid4()
        task = Task(
            id=task_id,
            external_id=f"ext-{task_id}",
            title=title,
            raw_text="test raw",
            normalized_text="test normalized",
        )
        session.add(task)
        await session.flush()
        return task_id

    async def test_payload_secrets_redacted(self, test_session) -> None:
        """TaskEventService.create redacts secrets in payload."""
        from app.db.enums import ActorType
        from app.services.task_event_service import TaskEventService

        task_id = await self._create_task(test_session)

        svc = TaskEventService(test_session)
        event = await svc.create(
            task_id=task_id,
            event_type="agent_selected",
            actor_type=ActorType.SYSTEM,
            payload={
                "agent": "backend",
                "token": FAKE_JWT,
                "config": {"db_url": FAKE_DB_URL},
            },
        )
        assert event is not None
        payload = event.payload
        # Sensitive key values redacted
        assert payload["token"] == "[REDACTED:SECRET]"
        # Nested URL redacted
        assert "[REDACTED:DB_PASSWORD]" in payload["config"]["db_url"]
        # Non-sensitive field preserved
        assert payload["agent"] == "backend"

    async def test_payload_empty_no_error(self, test_session) -> None:
        """Empty payload is handled without exception."""
        from app.services.task_event_service import TaskEventService

        task_id = await self._create_task(test_session, "test-empty")

        svc = TaskEventService(test_session)
        event = await svc.create(
            task_id=task_id,
            event_type="test",
            payload=None,
        )
        assert event is not None
        assert event.payload == {}

    async def test_payload_clean_unchanged(self, test_session) -> None:
        """Clean payload passes through unchanged."""
        from app.services.task_event_service import TaskEventService

        task_id = await self._create_task(test_session, "test-clean")

        svc = TaskEventService(test_session)
        clean_payload = {"status": "ok", "count": 5}
        event = await svc.create(
            task_id=task_id,
            event_type="test",
            payload=clean_payload,
        )
        assert event.payload == clean_payload
