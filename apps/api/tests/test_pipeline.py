"""Tests for plan pipeline trigger endpoint (WRK-02)."""

import pytest
from httpx import AsyncClient


@pytest.fixture
async def project_id(async_client: AsyncClient) -> str:
    resp = await async_client.post(
        "/projects",
        json={
            "slug": "proj-pipeline",
            "name": "Pipeline Project",
            "repo_path": "/tmp/repo",
            "memory_path": ".ai_memory/projects/proj-pipeline",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.fixture
async def agent_id(async_client: AsyncClient) -> str:
    resp = await async_client.post(
        "/agents",
        json={
            "slug": "backend-pipeline",
            "name": "Backend Pipeline",
            "role": "backend-architect",
            "system_prompt": "You are backend pipeline agent",
            "permissions": {"plan_only": True},
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_task(
    async_client: AsyncClient,
    *,
    project_id: str,
    agent_id: str,
    risk_level: str = "low",
    chat_id: int = 100,
    thread_id: int = 5,
) -> str:
    payload = {
        "title": "Pipeline task",
        "raw_text": "add healthcheck",
        "normalized_text": "add healthcheck",
        "risk_level": risk_level,
        "project_id": project_id,
        "agent_id": agent_id,
        "telegram_chat_id": chat_id,
        "telegram_thread_id": thread_id,
    }
    resp = await async_client.post("/tasks", json=payload)
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.anyio
async def test_trigger_plan_success(
    async_client: AsyncClient,
    project_id: str,
    agent_id: str,
) -> None:
    """trigger-plan should transition to routed and return 202."""
    task_id = await _create_task(async_client, project_id=project_id, agent_id=agent_id)

    resp = await async_client.post(f"/tasks/{task_id}/trigger-plan")
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "routed"
    assert data["id"] == task_id


@pytest.mark.anyio
async def test_trigger_plan_creates_event(
    async_client: AsyncClient,
    project_id: str,
    agent_id: str,
) -> None:
    """trigger-plan should create a plan_triggered event."""
    task_id = await _create_task(async_client, project_id=project_id, agent_id=agent_id)

    await async_client.post(f"/tasks/{task_id}/trigger-plan")

    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    assert events_resp.status_code == 200
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "plan_triggered" in event_types


@pytest.mark.anyio
async def test_trigger_plan_rejects_missing_project(
    async_client: AsyncClient,
    agent_id: str,
) -> None:
    """trigger-plan should reject task without project_id."""
    payload = {
        "title": "No project",
        "raw_text": "test",
        "normalized_text": "test",
        "risk_level": "low",
        "agent_id": agent_id,
    }
    resp = await async_client.post("/tasks", json=payload)
    task_id = resp.json()["id"]

    resp = await async_client.post(f"/tasks/{task_id}/trigger-plan")
    assert resp.status_code == 422
    assert "project_id" in resp.json()["detail"]


@pytest.mark.anyio
async def test_trigger_plan_rejects_missing_agent(
    async_client: AsyncClient,
    project_id: str,
) -> None:
    """trigger-plan should reject task without agent_id."""
    payload = {
        "title": "No agent",
        "raw_text": "test",
        "normalized_text": "test",
        "risk_level": "low",
        "project_id": project_id,
    }
    resp = await async_client.post("/tasks", json=payload)
    task_id = resp.json()["id"]

    resp = await async_client.post(f"/tasks/{task_id}/trigger-plan")
    assert resp.status_code == 422
    assert "agent_id" in resp.json()["detail"]


@pytest.mark.anyio
async def test_trigger_plan_404_for_missing_task(async_client: AsyncClient) -> None:
    """trigger-plan should return 404 for nonexistent task."""
    resp = await async_client.post("/tasks/00000000-0000-0000-0000-000000000000/trigger-plan")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_full_pipeline_created_to_planning(
    async_client: AsyncClient,
    project_id: str,
    agent_id: str,
) -> None:
    """Full pipeline: create → trigger-plan → plan → approved (low risk)."""
    task_id = await _create_task(
        async_client,
        project_id=project_id,
        agent_id=agent_id,
        risk_level="low",
    )

    # Step 1: trigger plan
    trigger_resp = await async_client.post(f"/tasks/{task_id}/trigger-plan")
    assert trigger_resp.status_code == 202
    assert trigger_resp.json()["status"] == "routed"

    # Step 2: call runtime plan (simulating worker)
    plan_resp = await async_client.post(f"/runtime/tasks/{task_id}/plan")
    assert plan_resp.status_code == 200
    assert plan_resp.json()["status"] == "approved"
    assert plan_resp.json()["plan_text"]

    # Step 3: verify events
    events_resp = await async_client.get(f"/events/tasks/{task_id}/events")
    event_types = [e["event_type"] for e in events_resp.json()]
    assert "task_created" in event_types
    assert "plan_triggered" in event_types
    assert "plan_generated" in event_types
