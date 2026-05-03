"""API test: event_type validation after WRK-03-hardening."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_event_type_rejects_invalid(async_client: AsyncClient) -> None:
    """POST /events/tasks/{id}/events must reject unapproved event_type."""
    resp = await async_client.post(
        "/events/tasks/00000000-0000-0000-0000-000000000001/events",
        json={
            "event_type": "fake_completed",
            "actor_type": "system",
        },
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_event_type_accepts_valid(async_client: AsyncClient) -> None:
    """POST /events/tasks/{id}/events must accept approved event_type."""
    create_task = await async_client.post(
        "/tasks",
        json={"title": "evt", "raw_text": "r", "normalized_text": "n"},
    )
    task_id = create_task.json()["id"]

    resp = await async_client.post(
        f"/events/tasks/{task_id}/events",
        json={
            "event_type": "security_violation",
            "actor_type": "system",
            "payload": {"reason": "denied"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["event_type"] == "security_violation"


@pytest.mark.anyio
async def test_event_type_accepts_sandbox_events(async_client: AsyncClient) -> None:
    """POST /events/tasks/{id}/events accepts WRK-04 sandbox events."""
    create_task = await async_client.post(
        "/tasks",
        json={"title": "evt", "raw_text": "r", "normalized_text": "n"},
    )
    task_id = create_task.json()["id"]

    for event_type in ("sandbox_timeout", "sandbox_error"):
        resp = await async_client.post(
            f"/events/tasks/{task_id}/events",
            json={
                "event_type": event_type,
                "actor_type": "system",
                "payload": {"error": "x"},
            },
        )
        assert resp.status_code == 200
        assert resp.json()["event_type"] == event_type
