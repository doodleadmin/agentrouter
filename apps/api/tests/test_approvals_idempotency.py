"""TG-03: Verify approval idempotency — approve/reject already-decided → 409."""

import pytest
from httpx import AsyncClient


@pytest.fixture
async def task_and_approval(async_client: AsyncClient) -> tuple[str, str]:
    """Create a task and pending approval; return (task_id, approval_id)."""
    resp = await async_client.post("/tasks", json={
        "title": "idempotency test",
        "raw_text": "raw text",
        "normalized_text": "norm text",
    })
    task_id = resp.json()["id"]
    resp = await async_client.post(
        f"/approvals/tasks/{task_id}/approvals",
        json={"action": "deploy_production"},
    )
    return task_id, resp.json()["id"]


@pytest.mark.anyio
async def test_second_approve_returns_409(async_client: AsyncClient, task_and_approval: tuple[str, str]) -> None:
    _, approval_id = task_and_approval
    # First approve succeeds
    r1 = await async_client.post(f"/approvals/{approval_id}/approve")
    assert r1.status_code == 200
    assert r1.json()["status"] == "approved"
    # Second approve → 409 Conflict
    r2 = await async_client.post(f"/approvals/{approval_id}/approve")
    assert r2.status_code == 409
    assert "already decided" in r2.json()["detail"].lower()


@pytest.mark.anyio
async def test_second_reject_returns_409(async_client: AsyncClient, task_and_approval: tuple[str, str]) -> None:
    _, approval_id = task_and_approval
    # First reject succeeds
    r1 = await async_client.post(f"/approvals/{approval_id}/reject", json={"reason": "no"})
    assert r1.status_code == 200
    assert r1.json()["status"] == "rejected"
    # Second reject → 409 Conflict
    r2 = await async_client.post(f"/approvals/{approval_id}/reject")
    assert r2.status_code == 409
    assert "already decided" in r2.json()["detail"].lower()


@pytest.mark.anyio
async def test_reject_after_approve_returns_409(async_client: AsyncClient, task_and_approval: tuple[str, str]) -> None:
    _, approval_id = task_and_approval
    # Approve
    await async_client.post(f"/approvals/{approval_id}/approve")
    # Reject after approve → 409
    r = await async_client.post(f"/approvals/{approval_id}/reject")
    assert r.status_code == 409


@pytest.mark.anyio
async def test_approve_after_reject_returns_409(async_client: AsyncClient, task_and_approval: tuple[str, str]) -> None:
    _, approval_id = task_and_approval
    # Reject
    await async_client.post(f"/approvals/{approval_id}/reject")
    # Approve after reject → 409
    r = await async_client.post(f"/approvals/{approval_id}/approve")
    assert r.status_code == 409


@pytest.mark.anyio
async def test_pending_approval_status_unchanged_after_idempotency_check(async_client: AsyncClient, task_and_approval: tuple[str, str]) -> None:
    """Verify the approval status field is unchanged after a rejected second attempt."""
    _, approval_id = task_and_approval
    # Approve once
    await async_client.post(f"/approvals/{approval_id}/approve")
    # Second attempt fails
    await async_client.post(f"/approvals/{approval_id}/approve")
    # GET still shows approved
    r = await async_client.get(f"/approvals/{approval_id}")
    assert r.json()["status"] == "approved"
