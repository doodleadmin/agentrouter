"""Tests for approvals router endpoints."""

import pytest
from httpx import AsyncClient


@pytest.fixture
async def existing_task_id(async_client: AsyncClient) -> str:
    resp = await async_client.post("/tasks", json={
        "title": "approval test", "raw_text": "raw", "normalized_text": "norm",
    })
    return resp.json()["id"]


@pytest.mark.anyio
async def test_create_approval(async_client: AsyncClient, existing_task_id: str) -> None:
    resp = await async_client.post(
        f"/approvals/tasks/{existing_task_id}/approvals",
        json={"action": "deploy_production"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["action"] == "deploy_production"
    assert data["status"] == "pending"


@pytest.mark.anyio
async def test_list_approvals_empty(async_client: AsyncClient, existing_task_id: str) -> None:
    resp = await async_client.get(f"/approvals/tasks/{existing_task_id}/approvals")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.anyio
async def test_list_approvals_after_create(async_client: AsyncClient, existing_task_id: str) -> None:
    await async_client.post(
        f"/approvals/tasks/{existing_task_id}/approvals",
        json={"action": "deploy_staging"},
    )
    resp = await async_client.get(f"/approvals/tasks/{existing_task_id}/approvals")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.anyio
async def test_approve_approval(async_client: AsyncClient, existing_task_id: str) -> None:
    create = await async_client.post(
        f"/approvals/tasks/{existing_task_id}/approvals",
        json={"action": "deploy_production"},
    )
    approval_id = create.json()["id"]
    resp = await async_client.post(f"/approvals/{approval_id}/approve")
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


@pytest.mark.anyio
async def test_reject_approval(async_client: AsyncClient, existing_task_id: str) -> None:
    create = await async_client.post(
        f"/approvals/tasks/{existing_task_id}/approvals",
        json={"action": "change_env"},
    )
    approval_id = create.json()["id"]
    resp = await async_client.post(f"/approvals/{approval_id}/reject", json={"reason": "too risky"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
    assert resp.json()["reason"] == "too risky"


@pytest.mark.anyio
async def test_double_approve_rejected(async_client: AsyncClient, existing_task_id: str) -> None:
    create = await async_client.post(
        f"/approvals/tasks/{existing_task_id}/approvals",
        json={"action": "run_migration"},
    )
    approval_id = create.json()["id"]
    # first approve
    await async_client.post(f"/approvals/{approval_id}/approve")
    # second approve should fail with 409 (already decided)
    resp = await async_client.post(f"/approvals/{approval_id}/approve")
    assert resp.status_code == 409


@pytest.mark.anyio
async def test_double_reject_rejected(async_client: AsyncClient, existing_task_id: str) -> None:
    create = await async_client.post(
        f"/approvals/tasks/{existing_task_id}/approvals",
        json={"action": "delete_files"},
    )
    approval_id = create.json()["id"]
    await async_client.post(f"/approvals/{approval_id}/reject")
    resp = await async_client.post(f"/approvals/{approval_id}/reject")
    assert resp.status_code == 409


@pytest.mark.anyio
async def test_approval_not_found(async_client: AsyncClient) -> None:
    resp = await async_client.get("/approvals/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_events_created_on_approve(async_client: AsyncClient, existing_task_id: str) -> None:
    create = await async_client.post(
        f"/approvals/tasks/{existing_task_id}/approvals",
        json={"action": "deploy_staging"},
    )
    approval_id = create.json()["id"]
    await async_client.post(f"/approvals/{approval_id}/approve")

    resp = await async_client.get(f"/events/tasks/{existing_task_id}/events")
    events = resp.json()
    event_types = [e["event_type"] for e in events]
    assert "approval_requested" in event_types
    assert "approval_granted" in event_types


@pytest.mark.anyio
async def test_events_list_all(async_client: AsyncClient) -> None:
    create = await async_client.post("/tasks", json={
        "title": "t", "raw_text": "r", "normalized_text": "n",
    })
    task_id = create.json()["id"]
    resp = await async_client.get("/events", params={"task_id": task_id})
    assert resp.status_code == 200
    assert len(resp.json()) == 1
