"""Tests for agent_plan task pipeline logic."""

from unittest.mock import MagicMock, patch

from app.tasks.agent_plan import _format_plan_message, generate_plan


def test_format_plan_message_approved() -> None:
    msg = _format_plan_message("task-0001", "approved", "## Plan\n1. Step one")
    assert "Plan ready" in msg
    assert "approved" in msg
    assert "Auto-approved" in msg


def test_format_plan_message_waiting_approval() -> None:
    msg = _format_plan_message("task-0001", "waiting_approval", "## Plan\n1. Step one")
    assert "waiting_approval" in msg
    assert "Waiting for approval" in msg


def test_format_plan_message_truncates_long_plan() -> None:
    long_plan = "x" * 1200
    msg = _format_plan_message("task-0001", "approved", long_plan)
    assert len(msg) < 1200  # should be truncated


def test_format_plan_message_empty_plan() -> None:
    msg = _format_plan_message("task-0001", "approved", "")
    assert "Plan ready" in msg


def test_generate_plan_dispatches_notification_on_success() -> None:
    """When backend returns a task with chat_id, notification should be dispatched."""

    mock_plan_resp = MagicMock()
    mock_plan_resp.status_code = 200
    mock_plan_resp.raise_for_status = MagicMock()
    mock_plan_resp.json.return_value = {
        "status": "approved",
        "plan_text": "## Plan\n1. Do stuff",
    }

    mock_task_resp = MagicMock()
    mock_task_resp.status_code = 200
    mock_task_resp.raise_for_status = MagicMock()
    mock_task_resp.json.return_value = {
        "telegram_chat_id": 100,
        "telegram_thread_id": 5,
    }

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.return_value = mock_plan_resp
    mock_client.get.return_value = mock_task_resp

    mock_send_task = MagicMock()

    with (
        patch("app.tasks.agent_plan.httpx.Client", return_value=mock_client),
        patch("app.tasks.agent_plan.celery_app") as mock_app,
    ):
        mock_app.send_task = mock_send_task

        result = generate_plan("fake-task-id")

    assert result["status"] == "ok"
    assert result["notification_sent"] is True
    mock_send_task.assert_called_once()
    call_kwargs = mock_send_task.call_args
    assert call_kwargs[1]["queue"] == "notifications"
    assert call_kwargs[1]["kwargs"]["chat_id"] == 100
    assert call_kwargs[1]["kwargs"]["thread_id"] == 5


def test_generate_plan_no_notification_without_chat_id() -> None:
    """When task has no chat_id, notification should be skipped."""

    mock_plan_resp = MagicMock()
    mock_plan_resp.status_code = 200
    mock_plan_resp.raise_for_status = MagicMock()
    mock_plan_resp.json.return_value = {
        "status": "approved",
        "plan_text": "## Plan",
    }

    mock_task_resp = MagicMock()
    mock_task_resp.status_code = 200
    mock_task_resp.raise_for_status = MagicMock()
    mock_task_resp.json.return_value = {
        "telegram_chat_id": None,
        "telegram_thread_id": None,
    }

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.return_value = mock_plan_resp
    mock_client.get.return_value = mock_task_resp

    mock_send_task = MagicMock()

    with (
        patch("app.tasks.agent_plan.httpx.Client", return_value=mock_client),
        patch("app.tasks.agent_plan.celery_app") as mock_app,
    ):
        mock_app.send_task = mock_send_task

        result = generate_plan("fake-task-id")

    assert result["status"] == "ok"
    assert result["notification_sent"] is False
    mock_send_task.assert_not_called()
