"""BE-04 guardrails tests (plan-only, fake runtime)."""

from __future__ import annotations

from uuid import UUID
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.config import settings
from app.integrations.opencode.client import FakeOpenCodeHttpClient, OpenCodeHttpPlanClient
from app.schemas.task_event import ALLOWED_EVENT_TYPES
from app.services.runtime_service import RuntimeService


@pytest.fixture(autouse=True)
def _reset_runtime_provider() -> None:
    settings.RUNTIME_PROVIDER = "stub"
    settings.OPENCODE_SERVER_URL = ""


async def _mk_task(async_client: AsyncClient, *, risk: str = "low", repo_path: str = "apps/api") -> str:
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
            "raw_text": "analyze token and create plan",
            "normalized_text": "analyze token and create plan",
            "risk_level": risk,
            "project_id": project.json()["id"],
            "agent_id": agent.json()["id"],
        },
    )
    return task.json()["id"]


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
    }
    assert required.issubset(ALLOWED_EVENT_TYPES)


@pytest.mark.anyio
async def test_fake_http_sse_success_and_dedupe(test_session, async_client: AsyncClient) -> None:
    task_id = await _mk_task(async_client, risk="low")
    settings.RUNTIME_PROVIDER = "opencode_http"
    settings.OPENCODE_SERVER_URL = "http://example.local"
    events = [
        {"type": "plan.delta", "event_id": "1", "text": "## Plan\n1. read\n"},
        {"type": "plan.delta", "event_id": "1", "text": "DUPLICATE"},
        {"type": "tool.call", "event_id": "2", "action": "read"},
        {"type": "plan.final", "event_id": "3"},
    ]
    svc = RuntimeService(test_session, runtime_transport_factory=lambda: FakeOpenCodeHttpClient(events))
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "approved"
    assert "DUPLICATE" not in (task.plan_text or "")
    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_event_received" in event_types
    assert "runtime_duplicate_event_ignored" in event_types


@pytest.mark.anyio
async def test_policy_blocked_unknown_tool(test_session, async_client: AsyncClient) -> None:
    task_id = await _mk_task(async_client, risk="low")
    events = [{"type": "tool.call", "event_id": "1", "action": "deploy"}, {"type": "plan.final", "event_id": "2"}]
    svc = RuntimeService(test_session, runtime_client=OpenCodeHttpPlanClient(FakeOpenCodeHttpClient(events)))
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"


@pytest.mark.anyio
async def test_timeout_malformed_and_runtime_error_paths(test_session, async_client: AsyncClient) -> None:
    task_timeout = await _mk_task(async_client, risk="low")
    svc_timeout = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(FakeOpenCodeHttpClient([{"type": "plan.delta", "event_id": "1", "text": "x"}])),
    )
    assert (await svc_timeout.generate_plan_for_task(UUID(task_timeout))).status == "failed"

    task_bad = await _mk_task(async_client, risk="low")
    svc_bad = RuntimeService(
        test_session,
        runtime_client=OpenCodeHttpPlanClient(FakeOpenCodeHttpClient([{"type": "weird", "event_id": "1"}])),
    )
    assert (await svc_bad.generate_plan_for_task(UUID(task_bad))).status == "failed"


@pytest.mark.anyio
async def test_secrets_redaction_runtime_request_and_events(test_session, async_client: AsyncClient) -> None:
    task_id = await _mk_task(async_client, risk="low")
    fake = FakeOpenCodeHttpClient(
        [
            {"type": "plan.delta", "event_id": "1", "text": "token=abc api_key=xyz"},
            {"type": "plan.final", "event_id": "2"},
        ]
    )
    svc = RuntimeService(test_session, runtime_client=OpenCodeHttpPlanClient(fake))
    task = await svc.generate_plan_for_task(UUID(task_id))
    plan_text = (task.plan_text or "").lower()
    assert "abc" not in plan_text
    assert "xyz" not in plan_text
    assert fake.last_payload is not None
    payload_text = str(fake.last_payload).lower()
    assert "abc" not in payload_text
    assert "xyz" not in payload_text

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    body = str(events_resp.json()).lower()
    assert "abc" not in body
    assert "xyz" not in body


@pytest.mark.anyio
async def test_redaction_private_key_and_bearer_values_not_leaked(test_session, async_client: AsyncClient) -> None:
    task_id = await _mk_task(async_client, risk="low")
    private_key = "-----BEGIN PRIVATE KEY-----\nVERYSECRET123\n-----END PRIVATE KEY-----"
    fake = FakeOpenCodeHttpClient(
        [
            {"type": "plan.delta", "event_id": "1", "text": f"Authorization: Bearer supertoken123 {private_key}"},
            {"type": "plan.final", "event_id": "2"},
        ]
    )
    svc = RuntimeService(test_session, runtime_client=OpenCodeHttpPlanClient(fake))
    task = await svc.generate_plan_for_task(UUID(task_id))
    plan = (task.plan_text or "")
    assert "supertoken123" not in plan
    assert "VERYSECRET123" not in plan
    assert "[REDACTED" in plan


@pytest.mark.anyio
async def test_idempotent_retry_no_duplicate_final_events(test_session, async_client: AsyncClient) -> None:
    task_id = await _mk_task(async_client, risk="medium")
    svc = RuntimeService(test_session, runtime_client=OpenCodeHttpPlanClient(FakeOpenCodeHttpClient([
        {"type": "plan.delta", "event_id": "1", "text": "## Plan"},
        {"type": "plan.final", "event_id": "2"},
    ])))
    await svc.generate_plan_for_task(UUID(task_id))
    task_second = await svc.generate_plan_for_task(UUID(task_id))
    assert task_second.status == "waiting_approval"


@pytest.mark.anyio
async def test_timeout_emits_retry_scheduled_events(test_session, async_client: AsyncClient) -> None:
    task_id = await _mk_task(async_client, risk="low")
    settings.RUNTIME_PROVIDER = "opencode_http"
    settings.OPENCODE_SERVER_URL = "http://example.local"
    svc = RuntimeService(
        test_session,
        runtime_transport_factory=lambda: FakeOpenCodeHttpClient([{"type": "plan.delta", "event_id": "1", "text": "only partial"}]),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "failed"
    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_retry_scheduled" in event_types


@pytest.mark.anyio
async def test_opencode_http_explicit_fake_transport_via_di_works(test_session, async_client: AsyncClient) -> None:
    settings.RUNTIME_PROVIDER = "opencode_http"
    settings.OPENCODE_SERVER_URL = "http://example.local"
    task_id = await _mk_task(async_client, risk="low")
    svc = RuntimeService(
        test_session,
        runtime_transport_factory=lambda: FakeOpenCodeHttpClient(
            [
                {"type": "plan.delta", "event_id": "1", "text": "## Plan\n1. test path\n"},
                {"type": "plan.final", "event_id": "2"},
            ]
        ),
    )
    task = await svc.generate_plan_for_task(UUID(task_id))
    assert task.status == "approved"


@pytest.mark.anyio
async def test_no_silent_fallback_to_stub_for_opencode_http(async_client: AsyncClient) -> None:
    settings.RUNTIME_PROVIDER = "opencode_http"
    settings.OPENCODE_SERVER_URL = "http://example.local"
    task_id = await _mk_task(async_client, risk="low")

    resp = await async_client.post(f"/runtime/tasks/{task_id}/plan")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "failed"
    assert not body.get("plan_text")

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "runtime_error" in event_types
    assert "plan_generated" not in event_types
