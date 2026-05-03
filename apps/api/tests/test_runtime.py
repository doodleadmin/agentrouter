"""Tests for BE-03 runtime adapter plan-only endpoint."""

import pytest
from httpx import AsyncClient


@pytest.fixture
async def project_id(async_client: AsyncClient) -> str:
    resp = await async_client.post(
        "/projects",
        json={
            "slug": "proj-runtime",
            "name": "Runtime Project",
            "repo_path": "/tmp/repo",
            "memory_path": ".ai_memory/projects/proj-runtime",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.fixture
async def agent_id(async_client: AsyncClient) -> str:
    resp = await async_client.post(
        "/agents",
        json={
            "slug": "backend-runtime",
            "name": "Backend Runtime",
            "role": "backend-architect",
            "system_prompt": "You are backend runtime agent",
            "permissions": {"plan_only": True},
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_task(
    async_client: AsyncClient,
    *,
    risk_level: str,
    project_id: str | None,
    agent_id: str | None,
) -> str:
    payload = {
        "title": "Plan endpoint task",
        "raw_text": "add healthcheck",
        "normalized_text": "add healthcheck",
        "risk_level": risk_level,
    }
    if project_id is not None:
        payload["project_id"] = project_id
    if agent_id is not None:
        payload["agent_id"] = agent_id

    resp = await async_client.post("/tasks", json=payload)
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.anyio
async def test_runtime_plan_low_risk_auto_approved(
    async_client: AsyncClient,
    project_id: str,
    agent_id: str,
) -> None:
    task_id = await _create_task(
        async_client,
        risk_level="low",
        project_id=project_id,
        agent_id=agent_id,
    )

    resp = await async_client.post(f"/runtime/tasks/{task_id}/plan")
    assert resp.status_code == 200
    data = resp.json()
    assert data["plan_text"]
    assert "## Plan" in data["plan_text"]
    assert data["status"] == "approved"


@pytest.mark.anyio
async def test_runtime_plan_medium_creates_approval(
    async_client: AsyncClient,
    project_id: str,
    agent_id: str,
) -> None:
    task_id = await _create_task(
        async_client,
        risk_level="medium",
        project_id=project_id,
        agent_id=agent_id,
    )

    plan_resp = await async_client.post(f"/runtime/tasks/{task_id}/plan")
    assert plan_resp.status_code == 200
    assert plan_resp.json()["status"] == "waiting_approval"

    approvals_resp = await async_client.get(f"/approvals/tasks/{task_id}/approvals")
    assert approvals_resp.status_code == 200
    approvals = approvals_resp.json()
    assert len(approvals) == 1
    assert approvals[0]["status"] == "pending"


@pytest.mark.anyio
async def test_runtime_plan_fails_without_project_id(async_client: AsyncClient, agent_id: str) -> None:
    task_id = await _create_task(
        async_client,
        risk_level="low",
        project_id=None,
        agent_id=agent_id,
    )

    resp = await async_client.post(f"/runtime/tasks/{task_id}/plan")
    assert resp.status_code == 422
    assert "project_id" in resp.json()["detail"]


@pytest.mark.anyio
async def test_runtime_plan_fails_without_agent_id(async_client: AsyncClient, project_id: str) -> None:
    task_id = await _create_task(
        async_client,
        risk_level="low",
        project_id=project_id,
        agent_id=None,
    )

    resp = await async_client.post(f"/runtime/tasks/{task_id}/plan")
    assert resp.status_code == 422
    assert "agent_id" in resp.json()["detail"]


@pytest.mark.anyio
async def test_runtime_plan_creates_events_and_saves_plan(
    async_client: AsyncClient,
    project_id: str,
    agent_id: str,
) -> None:
    task_id = await _create_task(
        async_client,
        risk_level="high",
        project_id=project_id,
        agent_id=agent_id,
    )

    plan_resp = await async_client.post(f"/runtime/tasks/{task_id}/plan")
    assert plan_resp.status_code == 200
    body = plan_resp.json()
    assert body["plan_text"]

    task_resp = await async_client.get(f"/tasks/{task_id}")
    assert task_resp.status_code == 200
    assert task_resp.json()["plan_text"]

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    assert events_resp.status_code == 200
    event_types = [event["event_type"] for event in events_resp.json()]
    assert "plan_generated" in event_types
    assert "approval_requested" in event_types
