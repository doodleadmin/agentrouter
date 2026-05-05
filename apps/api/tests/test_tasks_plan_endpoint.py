"""TG-03: Verify GET /tasks/{id}/plan and POST /tasks/{id}/callback-answer endpoints."""

import hashlib
import hmac
import time
from uuid import uuid4

import pytest
from httpx import AsyncClient

# ── helpers ────────────────────────────────────────────────────────────

def _make_callback_data(
    action: str,
    task_id: str,
    approval_id: str = "none",
    rev: int = 1,
    ttl: int = 300,
    secret: str = "",
) -> str:
    """Build a v1 callback_data string with signature."""
    exp = int(time.time()) + ttl
    base = f"1|{action}|{task_id}|{approval_id}|{rev}|{exp}"
    sig = hmac.new(secret.encode("utf-8"), base.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{base}|{sig}"


# ── /tasks/{id}/plan ───────────────────────────────────────────────────

@pytest.mark.anyio
async def test_get_plan_empty(async_client: AsyncClient) -> None:
    """Plan endpoint returns null plan_text for a task without a plan."""
    resp = await async_client.post("/tasks", json={
        "title": "plan test", "raw_text": "raw", "normalized_text": "norm",
    })
    task_id = resp.json()["id"]

    r = await async_client.get(f"/tasks/{task_id}/plan")
    assert r.status_code == 200
    data = r.json()
    assert data["task_id"] == task_id
    assert data["plan_text"] is None
    assert data["plan_version"] == 1
    assert data["status"] == "created"


@pytest.mark.anyio
async def test_get_plan_with_text(async_client: AsyncClient) -> None:
    """Plan endpoint returns plan_text when present."""
    resp = await async_client.post("/tasks", json={
        "title": "plan test", "raw_text": "raw", "normalized_text": "norm",
    })
    task_id = resp.json()["id"]

    # Set plan_text via PATCH
    await async_client.patch(f"/tasks/{task_id}", json={"plan_text": "Step 1: Do X\nStep 2: Do Y"})

    r = await async_client.get(f"/tasks/{task_id}/plan")
    assert r.status_code == 200
    data = r.json()
    assert data["plan_text"] == "Step 1: Do X\nStep 2: Do Y"
    assert data["plan_version"] == 1


@pytest.mark.anyio
async def test_get_plan_not_found(async_client: AsyncClient) -> None:
    """Plan endpoint returns 404 for unknown task."""
    r = await async_client.get(f"/tasks/{uuid4()}/plan")
    assert r.status_code == 404


# ── /tasks/{id}/callback-answer ────────────────────────────────────────

@pytest.mark.anyio
async def test_callback_answer_valid(async_client: AsyncClient) -> None:
    """Valid callback_data returns task state."""
    resp = await async_client.post("/tasks", json={
        "title": "cb test", "raw_text": "raw", "normalized_text": "norm",
    })
    task_id = resp.json()["id"]

    cb = _make_callback_data("show_plan", task_id)
    r = await async_client.post(f"/tasks/{task_id}/callback-answer", json={
        "callback_data": cb,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["task_id"] == task_id
    assert data["action_valid"] is True
    assert data["action"] == "show_plan"


@pytest.mark.anyio
async def test_callback_answer_invalid_signature(async_client: AsyncClient) -> None:
    """Tampered callback_data is rejected."""
    resp = await async_client.post("/tasks", json={
        "title": "cb test", "raw_text": "raw", "normalized_text": "norm",
    })
    task_id = resp.json()["id"]

    cb = _make_callback_data("show_plan", task_id)
    parts = cb.split("|")
    parts[-1] = "0" * 64  # replace signature
    tampered = "|".join(parts)

    r = await async_client.post(f"/tasks/{task_id}/callback-answer", json={
        "callback_data": tampered,
    })
    assert r.status_code == 200  # soft validation, returns error in payload
    data = r.json()
    assert data["action_valid"] is False
    assert "signature" in data.get("error", "").lower()


@pytest.mark.anyio
async def test_callback_answer_expired(async_client: AsyncClient) -> None:
    """Expired callback_data is rejected."""
    resp = await async_client.post("/tasks", json={
        "title": "cb test", "raw_text": "raw", "normalized_text": "norm",
    })
    task_id = resp.json()["id"]

    # Build expired callback (expiry in the past)
    exp = int(time.time()) - 60
    base = f"1|show_plan|{task_id}|none|1|{exp}"
    sig = hmac.new(b"", base.encode("utf-8"), hashlib.sha256).hexdigest()
    cb = f"{base}|{sig}"

    r = await async_client.post(f"/tasks/{task_id}/callback-answer", json={
        "callback_data": cb,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["action_valid"] is False
    assert "expired" in data.get("error", "").lower()


@pytest.mark.anyio
async def test_callback_answer_malformed(async_client: AsyncClient) -> None:
    """Malformed callback_data is rejected."""
    resp = await async_client.post("/tasks", json={
        "title": "cb test", "raw_text": "raw", "normalized_text": "norm",
    })
    task_id = resp.json()["id"]

    r = await async_client.post(f"/tasks/{task_id}/callback-answer", json={
        "callback_data": "garbage",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["action_valid"] is False
    assert "format" in data.get("error", "").lower()


@pytest.mark.anyio
async def test_callback_answer_task_not_found(async_client: AsyncClient) -> None:
    """Callback for non-existent task returns error."""
    fake_id = str(uuid4())
    cb = _make_callback_data("show_plan", fake_id)
    r = await async_client.post(f"/tasks/{fake_id}/callback-answer", json={
        "callback_data": cb,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["action_valid"] is False
    assert "not found" in data.get("error", "").lower()


@pytest.mark.anyio
async def test_callback_answer_with_chat_constraint(async_client: AsyncClient) -> None:
    """Callback with chat_id constraint validates correctly."""
    resp = await async_client.post("/tasks", json={
        "title": "cb test",
        "raw_text": "raw",
        "normalized_text": "norm",
        "telegram_chat_id": 12345,
    })
    task_id = resp.json()["id"]

    # Correct chat_id
    cb = _make_callback_data("refresh", task_id)
    r = await async_client.post(f"/tasks/{task_id}/callback-answer", json={
        "callback_data": cb,
        "telegram_chat_id": 12345,
    })
    assert r.status_code == 200
    assert r.json()["action_valid"] is True

    # Wrong chat_id
    r2 = await async_client.post(f"/tasks/{task_id}/callback-answer", json={
        "callback_data": cb,
        "telegram_chat_id": 99999,
    })
    assert r2.json()["action_valid"] is False
    assert "chat" in r2.json().get("error", "").lower()


@pytest.mark.anyio
async def test_callback_answer_with_approval(async_client: AsyncClient) -> None:
    """Callback with approval_id returns approval state."""
    resp = await async_client.post("/tasks", json={
        "title": "cb with approval",
        "raw_text": "raw",
        "normalized_text": "norm",
    })
    task_id = resp.json()["id"]

    # Create an approval
    ar = await async_client.post(
        f"/approvals/tasks/{task_id}/approvals",
        json={"action": "deploy_staging"},
    )
    approval_id = ar.json()["id"]

    cb = _make_callback_data("approve", task_id, approval_id=approval_id)
    r = await async_client.post(f"/tasks/{task_id}/callback-answer", json={
        "callback_data": cb,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["action_valid"] is True
    assert data["approval_id"] == approval_id
    assert data["approval_status"] == "pending"
    assert data["action"] == "approve"


@pytest.mark.anyio
async def test_callback_answer_approval_mismatch(async_client: AsyncClient) -> None:
    """Callback with mismatched approval_task returns error."""
    # Create two tasks
    r1 = await async_client.post("/tasks", json={
        "title": "task1", "raw_text": "r1", "normalized_text": "n1",
    })
    task1_id = r1.json()["id"]

    r2 = await async_client.post("/tasks", json={
        "title": "task2", "raw_text": "r2", "normalized_text": "n2",
    })
    task2_id = r2.json()["id"]

    # Create approval on task1
    ar = await async_client.post(
        f"/approvals/tasks/{task1_id}/approvals",
        json={"action": "deploy"},
    )
    approval_id = ar.json()["id"]

    # Send callback_answer to task2 but with task1's approval_id
    cb = _make_callback_data("approve", task1_id, approval_id=approval_id)
    r = await async_client.post(f"/tasks/{task2_id}/callback-answer", json={
        "callback_data": cb,
    })
    # The callback_data references task1, but endpoint path uses task2
    # The CB task_id is embedded in callback_data, but we validate against URL task_id
    # Both mismatch → task_id from path != task_id from callback_data
    # Actually, the validation is against path task_id (task2), but the approval is for task1
    # The approval_id check validates that approval.task_id == task2.id → mismatch
    data = r.json()
    assert data.get("error") is not None or data.get("action_valid") is False
