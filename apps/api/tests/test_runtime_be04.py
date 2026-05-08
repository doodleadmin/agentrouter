"""BE-04/BE-05 guardrails tests (plan-only, fake runtime)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from app.config import settings
from app.integrations.opencode.client import (
    FakeOpenCodeHttpClient,
    OpenCodeHttpPlanClient,
    RuntimeEventError,
)
from app.schemas.task_event import ALLOWED_EVENT_TYPES
from app.services.runtime_service import RuntimeService


@pytest.fixture(autouse=True)
def _reset_runtime_provider() -> None:
    settings.RUNTIME_PROVIDER = "stub"
    settings.OPENCODE_SERVER_URL = ""
    settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP = False


async def _mk_task(
    async_client: AsyncClient,
    *,
    risk: str = "low",
    repo_path: str = "apps/api",
    raw_text: str = "analyze token and create plan",
    normalized_text: str = "analyze token and create plan",
) -> str:
    suffix = uuid4().hex[:8]
    project = await async_client.post(
        "/projects",
        json={
            "slug": f"proj-{risk}-{repo_path.replace('/', '-')}-{suffix}",
            "name": "Runtime BE04",
            "repo_path": repo_path,
            "memory_path": ".ai_memory/projects/proj-runtime",
        },
    )
    agent = await async_client.post(
        "/agents",
        json={
            "slug": f"agent-{risk}-{repo_path.replace('/', '-')}-{suffix}",
            "name": "Runtime Agent",
            "role": "backend-architect",
            "system_prompt": "You are backend runtime agent",
            "permissions": {"plan_only": True},
        },
    )
    task = await async_client.post(
        "/tasks",
        json={
            "title": "Plan endpoint task",
            "raw_text": raw_text,
            "normalized_text": normalized_text,
            "risk_level": risk,
            "project_id": project.json()["id"],
            "agent_id": agent.json()["id"],
        },
    )
    return task.json()["id"]


# ── Existing BE-04 tests (unchanged semantics) ─────────────────────────


@pytest.mark.anyio
async def test_default_provider_is_stub(async_client: AsyncClient) -> None:
    settings.RUNTIME_PROVIDER = "stub"
    task_id = await _mk_task(async_client, risk="low")
    resp = await async_client.post(f"/runtime/tasks/{task_id}/plan")
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


@pytest.mark.anyio
async def test_unknown_provider_fails_closed(async_client: AsyncClient) -> None:
    settings.RUNTIME_PROVIDER = "unknown_provider"
    task_id = await _mk_task(async_client, risk="low")
    resp = await async_client.post(f"/runtime/tasks/{task_id}/plan")
    assert resp.status_code == 200
    assert resp.json()["status"] == "failed"


@pytest.mark.anyio
async def test_opencode_http_without_url_fails_closed(async_client: AsyncClient) -> None:
    settings.RUNTIME_PROVIDER = "opencode_http"
    settings.OPENCODE_SERVER_URL = ""
    task_id = await _mk_task(async_client, risk="low")
    resp = await async_client.post(f"/runtime/tasks/{task_id}/plan")
    assert resp.status_code == 200
    assert resp.json()["status"] == "failed"

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_error" in event_types
    assert "task_failed" in event_types


@pytest.mark.anyio
async def test_root_escape_attempt_blocked(async_client: AsyncClient) -> None:
    settings.RUNTIME_PROVIDER = "opencode_http"
    settings.OPENCODE_SERVER_URL = "http://example.local"
    task_id = await _mk_task(async_client, risk="low", repo_path="../outside")
    resp = await async_client.post(f"/runtime/tasks/{task_id}/plan")
    assert resp.status_code == 200
    assert resp.json()["status"] == "failed"


@pytest.mark.anyio
async def test_approval_invariants_low(async_client: AsyncClient) -> None:
    settings.RUNTIME_PROVIDER = "stub"
    low = await _mk_task(async_client, risk="low")
    assert (await async_client.post(f"/runtime/tasks/{low}/plan")).json()["status"] == "approved"


@pytest.mark.anyio
async def test_approval_invariants_medium(async_client: AsyncClient) -> None:
    settings.RUNTIME_PROVIDER = "stub"
    med = await _mk_task(async_client, risk="medium")
    assert (await async_client.post(f"/runtime/tasks/{med}/plan")).json()["status"] == "waiting_approval"


@pytest.mark.anyio
async def test_approval_invariants_high(async_client: AsyncClient) -> None:
    settings.RUNTIME_PROVIDER = "stub"
    high = await _mk_task(async_client, risk="high")
    assert (await async_client.post(f"/runtime/tasks/{high}/plan")).json()["status"] == "waiting_approval"


@pytest.mark.anyio
async def test_event_types_extended_present() -> None:
    required = {
        "runtime_session_created",
        "runtime_event_received",
        "policy_blocked",
        "runtime_error",
        "runtime_timeout",
        "runtime_retry_scheduled",
        "runtime_duplicate_event_ignored",
        "runtime_event_malformed",
        "runtime_event_truncated",
    }
    assert required.issubset(ALLOWED_EVENT_TYPES)


# ── mapper unit tests (OpenCode-native part types, BE-07) ────────────


@pytest.mark.anyio
async def test_sync_message_parts_map_to_plan_final() -> None:
    """BE-07: OpenCode-native text + step-finish → plan.delta + plan.final."""
    result = OpenCodeHttpPlanClient._map_message_response_to_events(
        {
            "info": {"id": "msg-1", "modelID": "test"},
            "parts": [
                {"type": "text", "text": "## Plan\n1. Step"},
                {"type": "step-finish", "reason": "stop"},
            ],
        }
    )
    assert result[0]["type"] == "plan.delta"
    assert result[0]["text"] == "## Plan\n1. Step"
    assert result[1]["type"] == "plan.final"


@pytest.mark.anyio
async def test_sync_message_info_field_is_ignored() -> None:
    """BE-07: response["info"] is skipped, not used for plan content."""
    result = OpenCodeHttpPlanClient._map_message_response_to_events(
        {
            "info": {"id": "msg-1", "modelID": "gpt-4", "providerID": "openai"},
            "parts": [
                {"type": "text", "text": "## Plan\n1. Do X"},
                {"type": "step-finish", "reason": "stop"},
            ],
        }
    )
    assert len(result) == 2
    assert result[0]["text"] == "## Plan\n1. Do X"


@pytest.mark.anyio
async def test_sync_message_content_fallback_removed_be07() -> None:
    """BE-07: response["content"] is NO LONGER a fallback — only parts works."""
    with pytest.raises(RuntimeEventError, match="runtime_event_malformed"):
        OpenCodeHttpPlanClient._map_message_response_to_events(
            {
                "content": [
                    {"type": "text", "text": "## Plan\n1. Step"},
                    {"type": "step-finish", "reason": "stop"},
                ]
            }
        )


@pytest.mark.anyio
async def test_sync_message_unknown_part_type_fails_closed() -> None:
    """BE-07: unknown part type → runtime_event_malformed → fail-closed."""
    with pytest.raises(RuntimeEventError, match="runtime_event_malformed"):
        OpenCodeHttpPlanClient._map_message_response_to_events(
            {"parts": [{"type": "some_unknown_type"}]}
        )


@pytest.mark.anyio
async def test_sync_message_malformed_response_fails_closed() -> None:
    with pytest.raises(RuntimeEventError, match="runtime_event_malformed"):
        OpenCodeHttpPlanClient._map_message_response_to_events({"parts": "not-a-list"})


@pytest.mark.anyio
async def test_sync_message_empty_parts_fails_runtime_error() -> None:
    """BE-07: empty parts array → runtime_error."""
    with pytest.raises(RuntimeEventError, match="runtime_error"):
        OpenCodeHttpPlanClient._map_message_response_to_events({"parts": []})


@pytest.mark.anyio
async def test_sync_message_only_reasoning_fails_runtime_error(
    test_session, async_client: AsyncClient
) -> None:
    """BE-07: only reasoning + step-finish (no text) → plan_text empty →
    caller raises runtime_error (integration flow)."""
    task_id = await _mk_task(async_client, risk="low")
    fake = FakeOpenCodeHttpClient(
        [
            {"type": "reasoning", "text": "Let me think about this..."},
            {"type": "step-finish", "reason": "stop"},
        ]
    )
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake, max_retries=0),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"
    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_error" in event_types


@pytest.mark.anyio
async def test_reasoning_never_appears_in_plan_delta() -> None:
    """BE-07: reasoning parts produce NO plan.delta events, text is never
    saved in mapped events."""
    result = OpenCodeHttpPlanClient._map_message_response_to_events(
        {
            "parts": [
                {"type": "step-start"},
                {"type": "reasoning", "text": "I need to check the API schema."},
                {"type": "reasoning", "text": "Also review auth middleware."},
                {"type": "text", "text": "## Plan\n1. Add healthcheck"},
                {"type": "step-finish", "reason": "stop"},
            ]
        }
    )
    # Only text part produces plan.delta, step-finish produces plan.final
    assert len(result) == 2
    assert result[0]["type"] == "plan.delta"
    assert result[0]["text"] == "## Plan\n1. Add healthcheck"
    assert result[1]["type"] == "plan.final"
    # No reasoning text anywhere in mapped events
    all_text = " ".join(str(e) for e in result)
    assert "check the API schema" not in all_text
    assert "auth middleware" not in all_text


@pytest.mark.anyio
async def test_step_start_is_skipped_in_events() -> None:
    """BE-07: step-start parts produce no mapped events."""
    result = OpenCodeHttpPlanClient._map_message_response_to_events(
        {
            "parts": [
                {"type": "step-start", "step": "plan"},
                {"type": "text", "text": "## Plan"},
                {"type": "step-finish", "reason": "stop"},
            ]
        }
    )
    assert len(result) == 2  # text + step-finish only


@pytest.mark.anyio
async def test_tool_part_maps_to_tool_call() -> None:
    """BE-07: tool part → tool.call with action/path."""
    result = OpenCodeHttpPlanClient._map_message_response_to_events(
        {
            "parts": [
                {"type": "tool", "action": "read", "path": "app/main.py"},
                {"type": "text", "text": "## Plan\n1. Check main.py"},
                {"type": "step-finish", "reason": "stop"},
            ]
        }
    )
    assert result[0]["type"] == "tool.call"
    assert result[0]["action"] == "read"
    assert result[0]["path"] == "app/main.py"
    assert result[1]["type"] == "plan.delta"
    assert result[2]["type"] == "plan.final"


@pytest.mark.anyio
async def test_sync_message_final_without_content_fails_closed(
    test_session, async_client: AsyncClient
) -> None:
    """BE-07: step-finish without text → plan_text empty → caller raises
    runtime_error (integration test through generate_plan)."""
    task_id = await _mk_task(async_client, risk="low")
    fake = FakeOpenCodeHttpClient(
        [{"type": "step-finish", "reason": "stop"}]
    )
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake, max_retries=0),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"
    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_error" in event_types


@pytest.mark.anyio
async def test_malformed_part_not_a_dict_fails() -> None:
    """BE-07: part that is not a dict → runtime_event_malformed."""
    with pytest.raises(RuntimeEventError, match="runtime_event_malformed"):
        OpenCodeHttpPlanClient._map_message_response_to_events(
            {"parts": ["not-a-dict"]}
        )


@pytest.mark.anyio
async def test_part_without_type_field_fails() -> None:
    """BE-07: part without 'type' key → runtime_event_malformed."""
    with pytest.raises(RuntimeEventError, match="runtime_event_malformed"):
        OpenCodeHttpPlanClient._map_message_response_to_events(
            {"parts": [{"text": "missing type"}]}
        )


@pytest.mark.anyio
async def test_fake_http_sse_success_and_dedupe(test_session, async_client: AsyncClient) -> None:
    task_id = await _mk_task(async_client, risk="low")
    settings.RUNTIME_PROVIDER = "opencode_http"
    settings.OPENCODE_SERVER_URL = "http://example.local"
    settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP = True
    events = [
        {"type": "text", "text": "## Plan\n1. read\n"},
        {"type": "text", "text": "EXTRA"},  # second text part
        {"type": "tool", "action": "read"},
        {"type": "step-finish", "reason": "stop"},
    ]
    svc = RuntimeService(
        test_session,
        runtime_transport_factory=lambda: FakeOpenCodeHttpClient(events),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "approved"
    assert "## Plan" in (task.plan_text or "")
    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_event_received" in event_types


@pytest.mark.anyio
async def test_policy_blocked_unknown_tool(test_session, async_client: AsyncClient) -> None:
    task_id = await _mk_task(async_client, risk="low")
    events = [
        {"type": "tool", "action": "deploy"},
        {"type": "text", "text": "## Plan\n1. deploy"},
        {"type": "step-finish", "reason": "stop"},
    ]
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(FakeOpenCodeHttpClient(events)),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"


@pytest.mark.anyio
async def test_timeout_malformed_and_runtime_error_paths(
    test_session, async_client: AsyncClient
) -> None:
    # Timeout: no step-finish → never completes
    task_timeout = await _mk_task(async_client, risk="low")
    svc_timeout = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(
            FakeOpenCodeHttpClient([{"type": "text", "text": "x"}])
        ),
    )
    assert (await svc_timeout.generate_plan_for_task(UUID(task_timeout))).status == "failed"

    # Unknown type in raw part → runtime_event_malformed
    task_bad = await _mk_task(async_client, risk="low")
    svc_bad = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(
            FakeOpenCodeHttpClient([{"type": "weird"}])
        ),
    )
    assert (await svc_bad.generate_plan_for_task(UUID(task_bad))).status == "failed"


@pytest.mark.anyio
async def test_secrets_redaction_runtime_request_and_events(
    test_session, async_client: AsyncClient
) -> None:
    task_id = await _mk_task(async_client, risk="low")
    secret_a = "tokensecret_abc123xyz"
    secret_b = "apikeysecret_xyz987abc"
    fake = FakeOpenCodeHttpClient(
        [
            {"type": "text", "text": f"token={secret_a} api_key={secret_b}"},
            {"type": "step-finish", "reason": "stop"},
        ]
    )
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    plan_text = (task.plan_text or "").lower()
    assert secret_a.lower() not in plan_text
    assert secret_b.lower() not in plan_text
    assert fake.last_payload is not None
    payload_text = str(fake.last_payload).lower()
    assert secret_a.lower() not in payload_text
    assert secret_b.lower() not in payload_text

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    body = str(events_resp.json()).lower()
    assert secret_a.lower() not in body
    assert secret_b.lower() not in body


@pytest.mark.anyio
async def test_redaction_private_key_and_bearer_values_not_leaked(
    test_session, async_client: AsyncClient
) -> None:
    task_id = await _mk_task(async_client, risk="low")
    private_key = "-----BEGIN PRIVATE KEY-----\nVERYSECRET123\n-----END PRIVATE KEY-----"
    fake = FakeOpenCodeHttpClient(
        [
            {
                "type": "text",
                "text": f"Authorization: Bearer supertoken123 {private_key}",
            },
            {"type": "step-finish", "reason": "stop"},
        ]
    )
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    plan = task.plan_text or ""
    assert "supertoken123" not in plan
    assert "VERYSECRET123" not in plan
    assert "[REDACTED" in plan


@pytest.mark.anyio
async def test_idempotent_retry_no_duplicate_final_events(
    test_session, async_client: AsyncClient
) -> None:
    task_id = await _mk_task(async_client, risk="medium")
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(
            FakeOpenCodeHttpClient([
                {"type": "text", "text": "## Plan"},
                {"type": "step-finish", "reason": "stop"},
            ])
        ),
    )
    await svc.generate_plan_for_task(UUID(task_id))
    task_second = await svc.generate_plan_for_task(UUID(task_id))
    assert task_second.status == "waiting_approval"


@pytest.mark.anyio
async def test_timeout_emits_retry_scheduled_events(
    test_session, async_client: AsyncClient
) -> None:
    task_id = await _mk_task(async_client, risk="low")
    settings.RUNTIME_PROVIDER = "opencode_http"
    settings.OPENCODE_SERVER_URL = "http://example.local"
    settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP = True
    svc = RuntimeService(
        test_session,
        runtime_transport_factory=lambda: FakeOpenCodeHttpClient(
            [{"type": "text", "text": "only partial"}]
        ),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"
    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_retry_scheduled" in event_types


@pytest.mark.anyio
async def test_opencode_http_explicit_fake_transport_via_di_works(
    test_session, async_client: AsyncClient
) -> None:
    settings.RUNTIME_PROVIDER = "opencode_http"
    settings.OPENCODE_SERVER_URL = "http://example.local"
    settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP = True
    task_id = await _mk_task(async_client, risk="low")
    svc = RuntimeService(
        test_session,
        runtime_transport_factory=lambda: FakeOpenCodeHttpClient(
            [
                {"type": "text", "text": "## Plan\n1. test path\n"},
                {"type": "step-finish", "reason": "stop"},
            ]
        ),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "approved"


@pytest.mark.anyio
async def test_no_silent_fallback_to_stub_for_opencode_http(
    async_client: AsyncClient,
) -> None:
    """B-1: opencode_http without allow flag must fail-closed — no silent stub fallback.

    Verifies:
    - Silent fallback to stub does NOT happen
    - Stub fingerprint ("plan-only", "No code execution") does NOT appear in plan_text
    - Error flows through runtime_error → task_failed
    - Provider remains opencode_http, not silently substituted
    """
    settings.RUNTIME_PROVIDER = "opencode_http"
    settings.OPENCODE_SERVER_URL = "http://example.local"
    # RUNTIME_ALLOW_REAL_OPENCODE_HTTP defaults to False → factory gate blocks
    task_id = await _mk_task(async_client, risk="low")

    resp = await async_client.post(f"/runtime/tasks/{task_id}/plan")
    assert resp.status_code == 200
    body = resp.json()

    # Task must fail, not succeed with stub output
    assert body["status"] == "failed"

    # No plan_text at all (factory blocks before any session is created)
    assert not body.get("plan_text")

    # Stub signature must NOT appear even if plan_text were set
    plan_text = body.get("plan_text") or ""
    assert "plan-only" not in plan_text
    assert "No code execution" not in plan_text

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]

    # Error flows through runtime_error → task_failed
    assert "runtime_error" in event_types
    assert "task_failed" in event_types
    assert "plan_generated" not in event_types

    # Provider was NOT silently substituted to stub
    assert settings.RUNTIME_PROVIDER == "opencode_http"


@pytest.mark.anyio
async def test_opencode_http_requires_url_and_allow_flag(async_client: AsyncClient) -> None:
    settings.RUNTIME_PROVIDER = "opencode_http"
    settings.OPENCODE_SERVER_URL = ""
    settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP = True
    task_without_url = await _mk_task(async_client, risk="low")
    resp_without_url = await async_client.post(f"/runtime/tasks/{task_without_url}/plan")
    assert resp_without_url.status_code == 200
    assert resp_without_url.json()["status"] == "failed"

    settings.RUNTIME_PROVIDER = "opencode_http"
    settings.OPENCODE_SERVER_URL = "http://example.local"
    settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP = False
    task_without_allow = await _mk_task(async_client, risk="low")
    resp_without_allow = await async_client.post(f"/runtime/tasks/{task_without_allow}/plan")
    assert resp_without_allow.status_code == 200
    assert resp_without_allow.json()["status"] == "failed"


def test_real_opencode_server_not_started_by_default_config() -> None:
    assert settings.RUNTIME_PROVIDER == "stub"
    assert settings.OPENCODE_SERVER_URL == ""
    assert settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP is False


# ═══════════════════════════════════════════════════════════════════════
# BE-05 NEW TESTS
# ═══════════════════════════════════════════════════════════════════════


# ── max_plan_size enforcement ───────────────────────────────────────────

@pytest.mark.anyio
async def test_max_plan_size_truncates_and_emits_warning(
    test_session, async_client: AsyncClient
) -> None:
    """Plan exceeding RUNTIME_MAX_PLAN_BYTES should be truncated with event."""
    task_id = await _mk_task(async_client, risk="low")
    # Build a giant plan delta that exceeds the limit
    huge_text = "A" * 200_000  # 200KB, exceeds default 100KB

    def _build_fake():
        return FakeOpenCodeHttpClient(
            [
                {"type": "text", "text": huge_text},
                {"type": "step-finish", "reason": "stop"},
            ]
        )

    # Use runtime_transport_factory so _on_event callback is wired
    settings.RUNTIME_PROVIDER = "opencode_http"
    settings.OPENCODE_SERVER_URL = "http://example.local"
    settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP = True
    svc = RuntimeService(
        test_session,
        runtime_transport_factory=_build_fake,
    )
    # Override max_plan_bytes via direct client injection after factory
    if hasattr(svc, "_runtime_client") and svc._runtime_client is None:
        pass  # factory creates client; we patch settings directly
    original_limit = settings.RUNTIME_MAX_PLAN_BYTES
    try:
        settings.RUNTIME_MAX_PLAN_BYTES = 1000  # force truncation
        task = await svc.generate_plan_for_task(UUID(task_id))
    finally:
        settings.RUNTIME_MAX_PLAN_BYTES = original_limit
    assert task.status == "approved"
    plan = task.plan_text or ""
    assert "[TRUNCATED" in plan
    assert "(session=fake-session-1)" in plan  # M-1: session_id in truncation marker
    assert len(plan.encode("utf-8")) <= 1500  # some margin for truncation marker

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_event_truncated" in event_types


@pytest.mark.anyio
async def test_max_plan_size_small_plan_not_truncated(
    test_session, async_client: AsyncClient
) -> None:
    """Small plan should pass through without truncation."""
    task_id = await _mk_task(async_client, risk="low")
    small_text = "## Small plan\nJust a few lines."
    fake = FakeOpenCodeHttpClient(
        [
            {"type": "text", "text": small_text},
            {"type": "step-finish", "reason": "stop"},
        ]
    )
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake, max_plan_bytes=100_000),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert "Small plan" in (task.plan_text or "")
    assert "[TRUNCATED" not in (task.plan_text or "")


# ── Client-side timeout enforcement ────────────────────────────────────

@pytest.mark.anyio
async def test_client_session_timeout_raises_failed(
    test_session, async_client: AsyncClient
) -> None:
    """Client-side session timeout should fail the task."""
    task_id = await _mk_task(async_client, risk="low")
    # No step-finish → timeout after session_timeout_sec
    fake = FakeOpenCodeHttpClient([
        {"type": "text", "text": "partial"},
    ])
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(
            fake,
            session_timeout_sec=0.0,  # immediate timeout
            max_retries=0,
        ),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_timeout" in event_types


# ── Tool path confinement ──────────────────────────────────────────────

@pytest.mark.anyio
async def test_tool_path_confinement_allowed_inside_root(
    test_session, async_client: AsyncClient
) -> None:
    """Tool call with path inside allowed root should succeed."""
    task_id = await _mk_task(async_client, risk="low", repo_path="apps/api")
    fake = FakeOpenCodeHttpClient(
        [
            {"type": "tool", "action": "read", "path": "app/main.py"},
            {"type": "text", "text": "## Plan\n1. ok"},
            {"type": "step-finish", "reason": "stop"},
        ]
    )
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "approved"


@pytest.mark.anyio
async def test_tool_path_confinement_blocks_escape(
    test_session, async_client: AsyncClient
) -> None:
    """Tool call with path escaping root should be blocked."""
    task_id = await _mk_task(async_client, risk="low", repo_path="apps/api")
    fake = FakeOpenCodeHttpClient(
        [
            {"type": "tool", "action": "read", "path": "../../etc/passwd"},
            {"type": "step-finish", "reason": "stop"},
        ]
    )
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "policy_blocked" in event_types


@pytest.mark.anyio
async def test_tool_path_confinement_blocks_unc_paths(
    test_session, async_client: AsyncClient
) -> None:
    """Tool call with UNC/network path should be blocked."""
    task_id = await _mk_task(async_client, risk="low", repo_path="apps/api")
    fake = FakeOpenCodeHttpClient(
        [
            {"type": "tool", "action": "search", "path": "\\\\evil\\share\\file"},
            {"type": "step-finish", "reason": "stop"},
        ]
    )
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"


@pytest.mark.anyio
async def test_tool_path_confinement_skips_without_path(
    test_session, async_client: AsyncClient
) -> None:
    """Tool call with read action but no path should not be blocked."""
    task_id = await _mk_task(async_client, risk="low")
    fake = FakeOpenCodeHttpClient(
        [
            {"type": "tool", "action": "read"},
            {"type": "text", "text": "## Plan\n1. ok"},
            {"type": "step-finish", "reason": "stop"},
        ]
    )
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "approved"


# ── SSE robustness ─────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_sse_malformed_missing_type_triggers_event_malformed(
    test_session, async_client: AsyncClient
) -> None:
    """Event with no 'type' field should trigger runtime_event_malformed."""
    task_id = await _mk_task(async_client, risk="low")
    fake = FakeOpenCodeHttpClient([
        {"text": "no type field"},
        {"type": "step-finish", "reason": "stop"},
    ])
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake, max_retries=0),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_event_malformed" in event_types


@pytest.mark.anyio
async def test_sse_unknown_event_type_triggers_runtime_error(
    test_session, async_client: AsyncClient
) -> None:
    """BE-07: unknown raw part type → runtime_event_malformed, fails task."""
    task_id = await _mk_task(async_client, risk="low")
    fake = FakeOpenCodeHttpClient([
        {"type": "file.update"},
        {"type": "text", "text": "## Plan"},
        {"type": "step-finish", "reason": "stop"},
    ])
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake, max_retries=0),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_event_malformed" in event_types


# ── Redaction: transport does NOT bypass existing redaction ─────────────

@pytest.mark.anyio
async def test_redaction_still_applied_after_transport_changes(
    test_session, async_client: AsyncClient
) -> None:
    """Verify that max_plan_size truncation does not bypass redaction."""
    task_id = await _mk_task(async_client, risk="low")
    original = settings.RUNTIME_MAX_PLAN_BYTES
    try:
        settings.RUNTIME_MAX_PLAN_BYTES = 500  # force truncation
        fake = FakeOpenCodeHttpClient(
            [
                {"type": "text", "text": "secret=abc123 " * 100},
                {"type": "step-finish", "reason": "stop"},
            ]
        )
        svc = RuntimeService(
            test_session,
            runtime_client=OpenCodeHttpPlanClient(fake),
        )
        task = await svc.generate_plan_for_task(UUID(task_id))
        plan = (task.plan_text or "").lower()
        assert "abc123" not in plan
        assert "[redacted:" in plan or "[TRUNCATED" in plan
    finally:
        settings.RUNTIME_MAX_PLAN_BYTES = original


# ── No silent fallback to stub preserved ───────────────────────────────

@pytest.mark.anyio
async def test_opencode_http_no_silent_fallback_with_transport(
    test_session, async_client: AsyncClient
) -> None:
    """When opencode_http is set and no DI is provided via API endpoint,
    the factory gate (RUNTIME_ALLOW_REAL_OPENCODE_HTTP=False) blocks
    creation of RealOpenCodeHttpTransport — fail-closed, no stub fallback."""
    settings.RUNTIME_PROVIDER = "opencode_http"
    settings.OPENCODE_SERVER_URL = "http://example.local"
    # RUNTIME_ALLOW_REAL_OPENCODE_HTTP defaults to False → factory blocks
    task_id = await _mk_task(async_client, risk="low")

    # Through API endpoint (no DI), factory gate raises RuntimeConfigurationError
    resp = await async_client.post(f"/runtime/tasks/{task_id}/plan")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "failed"
    assert not body.get("plan_text")

    # Stub signature must NOT appear
    plan_text = body.get("plan_text") or ""
    assert "plan-only" not in plan_text
    assert "No code execution" not in plan_text

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_error" in event_types
    assert "task_failed" in event_types
    assert "plan_generated" not in event_types

    # Provider not silently substituted
    assert settings.RUNTIME_PROVIDER == "opencode_http"


# ═══════════════════════════════════════════════════════════════════════
# BE-05 M-3 NEW TESTS — RUNTIME_ALLOW_REAL_OPENCODE_HTTP safety gate
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.anyio
async def test_opencode_http_without_allow_flag_fail_closed(
    async_client: AsyncClient,
) -> None:
    """M-3 test 3: opencode_http with URL but without RUNTIME_ALLOW_REAL_OPENCODE_HTTP
    must fail-closed (RuntimeConfigurationError → runtime_error → task_failed)."""
    settings.RUNTIME_PROVIDER = "opencode_http"
    settings.OPENCODE_SERVER_URL = "http://example.local"
    settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP = False
    task_id = await _mk_task(async_client, risk="low")

    resp = await async_client.post(f"/runtime/tasks/{task_id}/plan")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "failed"
    assert not body.get("plan_text")

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_error" in event_types
    assert "task_failed" in event_types
    assert "plan_generated" not in event_types

    # Provider not silently substituted
    assert settings.RUNTIME_PROVIDER == "opencode_http"


@pytest.mark.anyio
async def test_opencode_http_with_allow_unreachable_server_runtime_error(
    async_client: AsyncClient,
) -> None:
    """M-3 test 4: allow flag=True + unreachable server → factory creates real
    transport → connection fails → runtime_error/task_failed, no fallback to stub.

    Uses a mocked _build_client to avoid 10s connect timeout in tests.
    """
    settings.RUNTIME_PROVIDER = "opencode_http"
    settings.OPENCODE_SERVER_URL = "http://unreachable.local"
    settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP = True
    task_id = await _mk_task(async_client, risk="low")

    # Mock the transport's internal HTTP client to simulate connection failure

    import httpx

    from app.integrations.opencode.transport import RealOpenCodeHttpTransport

    mock_http_client = MagicMock()
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=None)
    mock_http_client.post = AsyncMock(
        side_effect=httpx.ConnectError("Connection refused")
    )

    with patch.object(
        RealOpenCodeHttpTransport, "_build_client", return_value=mock_http_client
    ):
        resp = await async_client.post(f"/runtime/tasks/{task_id}/plan")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "failed"
    assert not body.get("plan_text")

    # Stub signature must NOT appear
    plan_text = body.get("plan_text") or ""
    assert "plan-only" not in plan_text
    assert "No code execution" not in plan_text

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_error" in event_types
    assert "task_failed" in event_types
    assert "plan_generated" not in event_types

    # Provider not silently substituted to stub
    assert settings.RUNTIME_PROVIDER == "opencode_http"


@pytest.mark.anyio
async def test_real_opencode_server_not_started() -> None:
    """M-3 test 8: verify real OpenCode server is never started during tests.

    The RUNTIME_ALLOW_REAL_OPENCODE_HTTP defaults to False and no real
    HTTP connections are made to any OpenCode server. This test confirms
    the default state is safe.
    """
    assert settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP is False
    assert settings.RUNTIME_PROVIDER == "stub"
    assert settings.OPENCODE_SERVER_URL == ""


# ═══════════════════════════════════════════════════════════════════════
# BE-05 M-2 NEW TEST — SSE non-JSON chunk truncation via client
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.anyio
async def test_legacy_truncation_flag_in_delta_does_not_break_sync_flow(
    test_session, async_client: AsyncClient
) -> None:
    """Legacy `_sse_chunk_truncated` field is tolerated in sync message flow."""
    task_id = await _mk_task(async_client, risk="low")

    settings.RUNTIME_PROVIDER = "opencode_http"
    settings.OPENCODE_SERVER_URL = "http://example.local"
    settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP = True

    def _build_fake():
        return FakeOpenCodeHttpClient(
            [
                {
                    "type": "text",
                    "text": "hello",
                    "_sse_chunk_truncated": True,
                },
                {"type": "step-finish", "reason": "stop"},
            ]
        )

    svc = RuntimeService(
        test_session,
        runtime_transport_factory=_build_fake,
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "approved"

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "plan_generated" in event_types


# ═══════════════════════════════════════════════════════════════════════
# BE-07 NEW TESTS — OpenCode payload and response mapping alignment
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.anyio
async def test_be07_reasoning_text_never_in_plan_or_events(
    test_session, async_client: AsyncClient
) -> None:
    """BE-07: reasoning parts text must NOT appear in plan_text or task_events."""
    task_id = await _mk_task(async_client, risk="low")
    reasoning_text = "The API needs a healthcheck endpoint because of SLO requirements."
    fake = FakeOpenCodeHttpClient(
        [
            {"type": "step-start"},
            {"type": "reasoning", "text": reasoning_text},
            {"type": "text", "text": "## Plan\n1. Add /health endpoint\n2. Add tests"},
            {"type": "step-finish", "reason": "stop"},
        ]
    )
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "approved"

    # Reasoning text must NOT be in plan_text
    plan = (task.plan_text or "")
    assert "healthcheck endpoint" not in plan
    assert "SLO requirements" not in plan
    assert "/health" in plan  # from the text part

    # Reasoning text must NOT be in any task_events payload
    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    events_json_str = str(events_resp.json())
    assert "healthcheck endpoint" not in events_json_str
    assert "SLO requirements" not in events_json_str


@pytest.mark.anyio
async def test_be07_full_opencode_response_flow(
    test_session, async_client: AsyncClient
) -> None:
    """BE-07: real OpenCode response shape (text + reasoning + step-start +
    step-finish) → correct plan from text parts only."""
    task_id = await _mk_task(async_client, risk="low")
    fake = FakeOpenCodeHttpClient(
        [
            {"type": "step-start"},
            {"type": "reasoning", "text": "I need to analyze the task first."},
            {"type": "text", "text": "## Plan\n1. Analyze codebase\n"},
            {"type": "reasoning", "text": "Now I should think about tests."},
            {"type": "text", "text": "2. Write unit tests\n3. Validate\n"},
            {"type": "step-finish", "reason": "stop"},
        ]
    )
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "approved"

    # Plan should only contain text from text parts
    plan = task.plan_text or ""
    assert "1. Analyze codebase" in plan
    assert "2. Write unit tests" in plan
    # Reasoning text should not leak
    assert "I need to analyze" not in plan
    assert "think about tests" not in plan


@pytest.mark.anyio
async def test_be07_only_reasoning_parts_fails(
    test_session, async_client: AsyncClient
) -> None:
    """BE-07: only reasoning/step-start parts (no text) → runtime_error."""
    task_id = await _mk_task(async_client, risk="low")
    fake = FakeOpenCodeHttpClient(
        [
            {"type": "step-start"},
            {"type": "reasoning", "text": "Let me think about this."},
            {"type": "reasoning", "text": "More thinking..."},
            {"type": "step-finish", "reason": "stop"},
        ]
    )
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake, max_retries=0),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_error" in event_types


@pytest.mark.anyio
async def test_be07_empty_parts_fails(
    test_session, async_client: AsyncClient
) -> None:
    """BE-07: empty parts array → runtime_error."""
    task_id = await _mk_task(async_client, risk="low")
    fake = FakeOpenCodeHttpClient([])
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake, max_retries=0),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_error" in event_types


@pytest.mark.anyio
async def test_be07_malformed_parts_fails(
    test_session, async_client: AsyncClient
) -> None:
    """BE-07: malformed part (not a dict) → runtime_event_malformed."""
    task_id = await _mk_task(async_client, risk="low")
    fake = FakeOpenCodeHttpClient(["not-a-dict"])
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake, max_retries=0),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_event_malformed" in event_types


@pytest.mark.anyio
async def test_be07_unknown_part_type_fails(
    test_session, async_client: AsyncClient
) -> None:
    """BE-07: unknown part type → runtime_event_malformed."""
    task_id = await _mk_task(async_client, risk="low")
    fake = FakeOpenCodeHttpClient(
        [
            {"type": "some_unknown_type"},
            {"type": "text", "text": "plan"},
            {"type": "step-finish", "reason": "stop"},
        ]
    )
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake, max_retries=0),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_event_malformed" in event_types


@pytest.mark.anyio
async def test_be07_tool_mutating_blocked_by_policy(
    test_session, async_client: AsyncClient
) -> None:
    """BE-07: tool part with mutating action (deploy) → policy_blocked."""
    task_id = await _mk_task(async_client, risk="low")
    fake = FakeOpenCodeHttpClient(
        [
            {"type": "tool", "action": "deploy", "path": "/etc/config"},
            {"type": "text", "text": "## Plan\n1. deploy"},
            {"type": "step-finish", "reason": "stop"},
        ]
    )
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake, max_retries=0),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "policy_blocked" in event_types


@pytest.mark.anyio
async def test_be07_confirm_stub_is_default() -> None:
    """BE-07 guard: confirm default provider is stub, no real server started."""
    assert settings.RUNTIME_PROVIDER == "stub"
    assert settings.OPENCODE_SERVER_URL == ""
    assert settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP is False


# ═══════════════════════════════════════════════════════════════════════
# BE-08 TESTS — session traceability + timeout tuning
# ═══════════════════════════════════════════════════════════════════════


def test_be08_session_timeout_config_default_is_300() -> None:
    """BE-08/BE-10: RUNTIME_SESSION_TIMEOUT_SECONDS should default to 300
    (was 60 → BE-08 180 → BE-10 300 for real OpenCode headroom)."""
    assert settings.RUNTIME_SESSION_TIMEOUT_SECONDS == 300


@pytest.mark.anyio
async def test_be08_timeout_still_maps_to_runtime_error_and_task_failed(
    test_session, async_client: AsyncClient
) -> None:
    """BE-08: timeout still flows through runtime_timeout → task_failed."""
    task_id = await _mk_task(async_client, risk="low")
    # No step-finish → timeout after session_timeout_sec
    fake = FakeOpenCodeHttpClient([
        {"type": "text", "text": "partial"},
    ])
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(
            fake,
            session_timeout_sec=0.0,  # immediate timeout
            max_retries=0,
        ),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_timeout" in event_types
    assert "task_failed" in event_types


def test_be08_default_provider_still_stub() -> None:
    """BE-08 guard: default provider remains stub after changes."""
    assert settings.RUNTIME_PROVIDER == "stub"
    assert settings.OPENCODE_SERVER_URL == ""
    assert settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP is False


def test_be08_real_opencode_server_not_started() -> None:
    """BE-08 guard: confirm real OpenCode server is never started."""
    assert settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP is False
    assert settings.RUNTIME_PROVIDER == "stub"
    assert settings.OPENCODE_SERVER_URL == ""


# ═══════════════════════════════════════════════════════════════════════
# BE-10 TESTS — Runtime Reliability Hardening
# ═══════════════════════════════════════════════════════════════════════


# ── P0-1 / P0-2: Idempotency and no duplicate plan events ──────────────

@pytest.mark.anyio
async def test_be10_no_duplicate_plan_generated_on_repeated_call(
    test_session, async_client: AsyncClient
) -> None:
    """P0-1: Repeated POST /runtime/{id}/plan should only emit plan_generated once."""
    task_id = await _mk_task(async_client, risk="low")

    # First call — should succeed (stub auto-approves)
    resp1 = await async_client.post(f"/runtime/tasks/{task_id}/plan")
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "approved"

    # Second call — idempotent return, no duplicate work
    resp2 = await async_client.post(f"/runtime/tasks/{task_id}/plan")
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "approved"

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert event_types.count("plan_generated") == 1


@pytest.mark.anyio
async def test_be10_no_duplicate_approval_requested(
    test_session, async_client: AsyncClient
) -> None:
    """P0-1: Medium-risk task called twice should only request approval once."""
    task_id = await _mk_task(async_client, risk="medium")

    resp1 = await async_client.post(f"/runtime/tasks/{task_id}/plan")
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "waiting_approval"

    resp2 = await async_client.post(f"/runtime/tasks/{task_id}/plan")
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "waiting_approval"

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert event_types.count("approval_requested") == 1
    assert event_types.count("plan_generated") == 1


@pytest.mark.anyio
async def test_be10_planning_status_guards_concurrent_reentry(
    test_session, async_client: AsyncClient
) -> None:
    """P0-1: Task in PLANNING status should return idempotently without duplicate work."""
    from app.db.enums import TaskStatus
    from app.schemas.task import TaskStatusUpdate
    from app.services.task_service import TaskService

    task_id = await _mk_task(async_client, risk="low")
    tsvc = TaskService(test_session)

    # First, transition task to PLANNING manually (simulate in-flight)
    await tsvc.update_status(UUID(task_id), TaskStatusUpdate(status=TaskStatus.PLANNING))

    # Call plan endpoint — should see PLANNING, return existing task
    resp = await async_client.post(f"/runtime/tasks/{task_id}/plan")
    assert resp.status_code == 200
    # Should not have plan_generated — returned early from idempotency guard
    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "plan_generated" not in event_types


@pytest.mark.anyio
async def test_be10_trigger_plan_only_accepts_created(
    test_session, async_client: AsyncClient
) -> None:
    """P0-2: trigger-plan endpoint should reject non-CREATED tasks with 409."""
    task_id = await _mk_task(async_client, risk="low")

    # First trigger-plan succeeds (CREATED → ROUTED)
    resp1 = await async_client.post(f"/tasks/{task_id}/trigger-plan")
    assert resp1.status_code == 202

    # Second trigger-plan should reject (status is now ROUTED, not CREATED)
    resp2 = await async_client.post(f"/tasks/{task_id}/trigger-plan")
    assert resp2.status_code == 409
    assert "already triggered" in resp2.json()["detail"].lower()


# ── P2-5: Event ordering — session_created before events ───────────────

@pytest.mark.anyio
async def test_be10_session_created_before_events(
    test_session, async_client: AsyncClient
) -> None:
    """P2-5: runtime_session_created must appear before runtime_event_received in audit."""
    task_id = await _mk_task(async_client, risk="low")
    fake = FakeOpenCodeHttpClient(
        [
            {"type": "text", "text": "## Plan\n1. Step"},
            {"type": "step-finish", "reason": "stop"},
        ]
    )
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake, max_retries=0),
    )
    await svc.generate_plan_for_task(UUID(task_id))

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    events = events_resp.json()
    [e["event_type"] for e in events]

    # session_created must appear before any runtime_event_received
    session_idx = next((i for i, e in enumerate(events) if e["event_type"] == "runtime_session_created"), None)
    event_received_idxs = [i for i, e in enumerate(events) if e["event_type"] == "runtime_event_received"]

    assert session_idx is not None, "runtime_session_created event missing"
    if event_received_idxs:
        assert session_idx < event_received_idxs[0], (
            f"runtime_session_created (idx={session_idx}) must be before "
            f"first runtime_event_received (idx={event_received_idxs[0]})"
        )


# ── P1-4: Retry exception handling ─────────────────────────────────────

@pytest.mark.anyio
async def test_be10_retry_scheduled_includes_attempt(
    test_session, async_client: AsyncClient
) -> None:
    """P1-4: runtime_retry_scheduled event payload must include attempt as int."""
    task_id = await _mk_task(async_client, risk="low")
    # No step-finish → timeout → retry scheduled
    fake = FakeOpenCodeHttpClient([{"type": "text", "text": "partial"}])
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake, max_retries=2),
    )
    await svc.generate_plan_for_task(UUID(task_id))

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    events = events_resp.json()
    retry_events = [e for e in events if e["event_type"] == "runtime_retry_scheduled"]

    assert len(retry_events) >= 1, "Expected at least one runtime_retry_scheduled"
    for evt in retry_events:
        payload = evt.get("payload") or {}
        assert "attempt" in payload, f"Missing 'attempt' in retry payload: {payload}"
        assert isinstance(payload["attempt"], int), f"attempt should be int, got {type(payload['attempt'])}"


@pytest.mark.anyio
async def test_be10_transport_timeout_is_retried(
    test_session, async_client: AsyncClient
) -> None:
    """P1-4: Transport raising OpenCodeTimeoutError should trigger retry."""

    from app.integrations.opencode.transport import OpenCodeTimeoutError

    task_id = await _mk_task(async_client, risk="low")

    # Transport: create_session succeeds, send_message times out
    mock_transport = MagicMock()
    mock_transport.create_session = AsyncMock(return_value="fake-session-retry")
    mock_transport.send_message = AsyncMock(side_effect=OpenCodeTimeoutError("timed out"))

    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(mock_transport, max_retries=2),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_retry_scheduled" in event_types
    # Should have attempted retry (attempted retry_count times then fail)
    retry_events = [e for e in events_resp.json() if e["event_type"] == "runtime_retry_scheduled"]
    # With max_retries=2, attempts 1 and 2 → 2 retry events
    assert len(retry_events) >= 1


@pytest.mark.anyio
async def test_be10_non_retryable_400_fails_without_retry(
    test_session, async_client: AsyncClient
) -> None:
    """P1-4: Permanent HTTP 400 errors must NOT trigger retry (fail fast)."""

    from httpx import Response

    from app.integrations.opencode.transport import OpenCodeHTTPError

    task_id = await _mk_task(async_client, risk="low")

    # Simulate 400 response
    Response(status_code=400, json={"error": "bad request"})
    mock_transport = MagicMock()
    mock_transport.create_session = AsyncMock(return_value="fake-session-400")
    mock_transport.send_message = AsyncMock(
        side_effect=OpenCodeHTTPError("400 Bad Request")
    )

    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(mock_transport, max_retries=2),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    # Must NOT have retry events for permanent errors
    assert "runtime_retry_scheduled" not in event_types


@pytest.mark.anyio
async def test_be10_successful_plan_not_overwritten(
    test_session, async_client: AsyncClient
) -> None:
    """P0-1: Successful plan must survive a subsequent call with failing transport."""
    task_id = await _mk_task(async_client, risk="low")
    success_text = "## Plan\n1. Valid analysis\n2. Tests added"

    # First call: succeeds with valid plan
    fake1 = FakeOpenCodeHttpClient(
        [
            {"type": "text", "text": success_text},
            {"type": "step-finish", "reason": "stop"},
        ]
    )
    svc1 = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake1),
    )
    task = await svc1.generate_plan_for_task(UUID(task_id))
    assert task.status == "approved"
    assert "Valid analysis" in (task.plan_text or "")

    # Second call: idempotent guard returns task immediately
    # No transport is called because status is APPROVED
    task2 = await svc1.generate_plan_for_task(UUID(task_id))
    assert task2.status == "approved"
    assert "Valid analysis" in (task2.plan_text or "")

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert event_types.count("plan_generated") == 1


# ── P2-6: Timeout alignment ────────────────────────────────────────────

def test_be10_session_timeout_default_is_300() -> None:
    """P2-6: RUNTIME_SESSION_TIMEOUT_SECONDS should default to 300 (was 180)."""
    assert settings.RUNTIME_SESSION_TIMEOUT_SECONDS == 300


# ── Guards: default provider and no reasoning stored ───────────────────

@pytest.mark.anyio
async def test_be10_default_provider_stub() -> None:
    """BE-10 guard: confirm default provider is stub."""
    assert settings.RUNTIME_PROVIDER == "stub"
    assert settings.OPENCODE_SERVER_URL == ""
    assert settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP is False


@pytest.mark.anyio
async def test_be10_no_reasoning_stored(
    test_session, async_client: AsyncClient
) -> None:
    """BE-10: reasoning parts must NOT appear in plan_text or events, even in BE-10 changes."""
    task_id = await _mk_task(async_client, risk="low")
    reasoning_secret = "The API needs JWT validation middleware first."
    fake = FakeOpenCodeHttpClient(
        [
            {"type": "step-start"},
            {"type": "reasoning", "text": reasoning_secret},
            {"type": "text", "text": "## Plan\n1. Add /health"},
            {"type": "step-finish", "reason": "stop"},
        ]
    )
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(fake),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "approved"
    assert reasoning_secret not in (task.plan_text or "")
    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    events_str = str(events_resp.json())
    assert reasoning_secret not in events_str


# ═══════════════════════════════════════════════════════════════════════
# BE-12 P3 NEW TESTS — asyncio.wait_for enforcement in send_message flow
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.anyio
async def test_be12_send_message_wait_for_timeout_enforcement(
    test_session, async_client: AsyncClient
) -> None:
    """BE-12 P3: verify that asyncio.wait_for with _session_timeout is
    enforced in generate_plan flow.

    Mock transport.send_message to hang indefinitely (never-resolving future).
    The client's generate_plan must use asyncio.wait_for to bound the call
    with _session_timeout, raising TimeoutError. Without this protection,
    a hanging OpenCode server would permanently block the API worker.
    """
    from app.integrations.opencode.transport import OpenCodeTimeoutError

    task_id = await _mk_task(async_client, risk="low")

    # Transport that never resolves send_message (simulates hung server)
    mock_transport = MagicMock()
    mock_transport.create_session = AsyncMock(return_value="fake-session-hung")

    # Create a future that never resolves (simulates infinite hang)
    import asyncio as asyncio_mod

    hung_future: asyncio_mod.Future[dict[str, Any]] = asyncio_mod.Future()
    mock_transport.send_message = MagicMock(return_value=hung_future)

    # Use a short session_timeout so the test doesn't hang
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(
            mock_transport,
            max_retries=0,
            session_timeout_sec=0.05,  # 50ms timeout
        ),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    # TimeoutError from asyncio.wait_for → runtime_timeout
    assert "runtime_timeout" in event_types, (
        f"Expected runtime_timeout in events, got {event_types}"
    )


@pytest.mark.anyio
async def test_be12_send_message_wait_for_not_hung_by_slow_transport(
    test_session, async_client: AsyncClient
) -> None:
    """BE-12 P3: verify that asyncio.wait_for does NOT cancel a transport
    that completes within the timeout window.

    A transport that returns a valid response within the session timeout
    must succeed normally — not be falsely timed out.
    """
    task_id = await _mk_task(async_client, risk="low")
    mock_transport = MagicMock()
    mock_transport.create_session = AsyncMock(return_value="fake-session-normal")

    valid_response = {
        "parts": [
            {"type": "text", "text": "## Plan\n1. Do something"},
            {"type": "step-finish", "reason": "stop"},
        ]
    }
    mock_transport.send_message = AsyncMock(return_value=valid_response)

    # Long enough timeout that the mock's immediate response completes
    svc = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(
            mock_transport,
            max_retries=0,
            session_timeout_sec=5.0,  # 5s — mock responds instantly
        ),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "approved"
    assert "Do something" in (task.plan_text or "")
