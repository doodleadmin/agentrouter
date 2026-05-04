"""Tests for tasks router endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_create_task(async_client: AsyncClient) -> None:
    resp = await async_client.post("/tasks", json={
        "title": "Add healthcheck",
        "raw_text": "add healthcheck endpoint",
        "normalized_text": "add healthcheck endpoint",
        "risk_level": "low",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["external_id"] == "task-0001"
    assert data["status"] == "created"
    assert data["risk_level"] == "low"


@pytest.mark.anyio
async def test_create_task_defaults(async_client: AsyncClient) -> None:
    resp = await async_client.post("/tasks", json={
        "title": "test",
        "raw_text": "raw",
        "normalized_text": "norm",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["risk_level"] == "low"
    assert data["status"] == "created"


@pytest.mark.anyio
async def test_create_task_validation(async_client: AsyncClient) -> None:
    resp = await async_client.post("/tasks", json={
        "title": "",  # too short
        "raw_text": "raw",
        "normalized_text": "norm",
    })
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_list_tasks_empty(async_client: AsyncClient) -> None:
    resp = await async_client.get("/tasks")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.anyio
async def test_list_tasks_after_create(async_client: AsyncClient) -> None:
    await async_client.post("/tasks", json={
        "title": "t1", "raw_text": "r1", "normalized_text": "n1",
    })
    resp = await async_client.get("/tasks")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.anyio
async def test_get_task(async_client: AsyncClient) -> None:
    create = await async_client.post("/tasks", json={
        "title": "get me", "raw_text": "r", "normalized_text": "n",
    })
    task_id = create.json()["id"]
    resp = await async_client.get(f"/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "get me"


@pytest.mark.anyio
async def test_get_task_404(async_client: AsyncClient) -> None:
    resp = await async_client.get("/tasks/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_update_task(async_client: AsyncClient) -> None:
    create = await async_client.post("/tasks", json={
        "title": "old", "raw_text": "r", "normalized_text": "n",
    })
    task_id = create.json()["id"]
    resp = await async_client.patch(f"/tasks/{task_id}", json={"title": "new"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "new"


@pytest.mark.anyio
async def test_status_transition_valid(async_client: AsyncClient) -> None:
    create = await async_client.post("/tasks", json={
        "title": "t", "raw_text": "r", "normalized_text": "n",
    })
    task_id = create.json()["id"]
    # created -> routed
    resp = await async_client.patch(f"/tasks/{task_id}/status", json={"status": "routed"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "routed"


@pytest.mark.anyio
async def test_status_transition_invalid(async_client: AsyncClient) -> None:
    create = await async_client.post("/tasks", json={
        "title": "t", "raw_text": "r", "normalized_text": "n",
    })
    task_id = create.json()["id"]
    # created -> running: illegal
    resp = await async_client.patch(f"/tasks/{task_id}/status", json={"status": "running"})
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_cancel_task(async_client: AsyncClient) -> None:
    create = await async_client.post("/tasks", json={
        "title": "t", "raw_text": "r", "normalized_text": "n",
    })
    task_id = create.json()["id"]
    resp = await async_client.post(f"/tasks/{task_id}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


@pytest.mark.anyio
async def test_cancel_already_terminal(async_client: AsyncClient) -> None:
    create = await async_client.post("/tasks", json={
        "title": "t", "raw_text": "r", "normalized_text": "n",
    })
    task_id = create.json()["id"]
    await async_client.post(f"/tasks/{task_id}/cancel")  # first cancel
    resp = await async_client.post(f"/tasks/{task_id}/cancel")  # second
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


@pytest.mark.anyio
async def test_list_tasks_filter_status(async_client: AsyncClient) -> None:
    await async_client.post("/tasks", json={
        "title": "t1", "raw_text": "r1", "normalized_text": "n1",
    })
    await async_client.post("/tasks", json={
        "title": "t2", "raw_text": "r2", "normalized_text": "n2",
    })
    resp = await async_client.get("/tasks", params={"status": "created"})
    assert resp.status_code == 200
    assert all(t["status"] == "created" for t in resp.json())


@pytest.mark.anyio
async def test_events_created_on_create(async_client: AsyncClient) -> None:
    create = await async_client.post("/tasks", json={
        "title": "t", "raw_text": "r", "normalized_text": "n",
    })
    task_id = create.json()["id"]
    resp = await async_client.get(f"/events/tasks/{task_id}/events")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) == 1
    assert events[0]["event_type"] == "task_created"


@pytest.mark.anyio
async def test_create_task_with_project_and_agent_persists(async_client: AsyncClient) -> None:
    project = await async_client.post(
        "/projects",
        json={
            "slug": "task-proj",
            "name": "Task Proj",
            "repo_path": "apps/api",
            "memory_path": ".ai_memory/projects/task-proj",
        },
    )
    agent = await async_client.post(
        "/agents",
        json={
            "slug": "task-agent",
            "name": "Task Agent",
            "role": "backend-architect",
            "system_prompt": "You are backend runtime agent",
            "permissions": {"plan_only": True},
        },
    )
    assert project.status_code == 201
    assert agent.status_code == 201

    task = await async_client.post(
        "/tasks",
        json={
            "title": "task refs",
            "raw_text": "r",
            "normalized_text": "n",
            "risk_level": "low",
            "project_id": project.json()["id"],
            "agent_id": agent.json()["id"],
        },
    )
    assert task.status_code == 201
    task_id = task.json()["id"]

    fetched = await async_client.get(f"/tasks/{task_id}")
    assert fetched.status_code == 200
    assert fetched.json()["project_id"] == project.json()["id"]
    assert fetched.json()["agent_id"] == agent.json()["id"]


@pytest.mark.anyio
async def test_create_task_invalid_fk_returns_422_or_409(async_client: AsyncClient) -> None:
    bad = await async_client.post(
        "/tasks",
        json={
            "title": "bad fk",
            "raw_text": "r",
            "normalized_text": "n",
            "project_id": "00000000-0000-0000-0000-000000000111",
            "agent_id": "00000000-0000-0000-0000-000000000222",
        },
    )
    assert bad.status_code in (422, 409)
    body = bad.text.lower()
    assert "traceback" not in body
    assert "select " not in body
    assert "insert " not in body


@pytest.mark.anyio
async def test_failed_task_create_rolls_back(async_client: AsyncClient) -> None:
    before = await async_client.get("/tasks")
    before_count = len(before.json())

    _ = await async_client.post(
        "/tasks",
        json={
            "title": "bad fk",
            "raw_text": "r",
            "normalized_text": "n",
            "project_id": "00000000-0000-0000-0000-00000000aaaa",
            "agent_id": "00000000-0000-0000-0000-00000000bbbb",
        },
    )

    after = await async_client.get("/tasks")
    assert len(after.json()) == before_count
