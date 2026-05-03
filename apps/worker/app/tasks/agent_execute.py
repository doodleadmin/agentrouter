"""Agent execute task — WRK-03 safe execute pipeline.

This implementation is intentionally sandbox-fake only:
- requires task.status == approved
- validates worktree boundary
- validates command policy
- writes audit events via API
- updates task status approved -> running -> completed|failed
"""

from __future__ import annotations

import logging
import shlex
from typing import Any

import httpx

from app.celery_app import celery_app
from app.config import settings
from app.queues import AGENT_EXECUTE
from app.services.command_policy import CommandPolicyError, validate_command
from app.services.redaction import redact_text
from app.services.sandbox_runner import (
    DockerSandboxRunner,
    DockerUnavailableError,
    FakeSandboxRunner,
    SandboxRunner,
    SandboxTimeoutError,
)
from app.services.worktree_policy import (
    WorktreePolicyError,
    build_worktree_path,
    validate_worktree_path,
)

logger = logging.getLogger(__name__)


def _task_url(task_id: str) -> str:
    return f"{settings.API_BASE_URL}/tasks/{task_id}"


def _task_status_url(task_id: str) -> str:
    return f"{settings.API_BASE_URL}/tasks/{task_id}/status"


def _task_events_url(task_id: str) -> str:
    return f"{settings.API_BASE_URL}/events/tasks/{task_id}/events"


def _post_event(client: httpx.Client, task_id: str, event_type: str, payload: dict[str, Any] | None = None) -> None:
    client.post(
        _task_events_url(task_id),
        json={
            "event_type": event_type,
            "actor_type": "system",
            "payload": payload or {},
        },
    ).raise_for_status()


def _patch_status(client: httpx.Client, task_id: str, status: str) -> None:
    client.patch(_task_status_url(task_id), json={"status": status}).raise_for_status()


def _patch_task_result(
    client: httpx.Client,
    task_id: str,
    *,
    worktree_path: str,
    result_summary: str,
    payload: dict[str, Any],
) -> None:
    client.patch(
        _task_url(task_id),
        json={
            "worktree_path": worktree_path,
            "result_summary": result_summary,
            "payload": payload,
        },
    ).raise_for_status()


def _pick_command(task_data: dict[str, Any]) -> str:
    payload = task_data.get("payload") or {}
    command = payload.get("command")
    if isinstance(command, str) and command.strip():
        return command.strip()
    return "pytest"


def _to_argv(command: str) -> list[str]:
    try:
        argv = shlex.split(command, posix=True)
    except ValueError as exc:
        raise CommandPolicyError(f"Failed to parse command argv: {exc}") from exc
    if not argv:
        raise CommandPolicyError("Command argv is empty")
    return argv


def _resolve_runner() -> tuple[SandboxRunner, str]:
    mode = settings.SANDBOX_RUNNER_MODE.strip().lower()
    if mode == "docker":
        return DockerSandboxRunner(), "docker"
    return FakeSandboxRunner(), "fake"


def _result_summary(*, runner_mode: str, success: bool) -> str:
    state = "completed" if success else "failed"
    return f"Execution {state} in {runner_mode} sandbox."


def _fail_with_security_violation(
    *,
    client: httpx.Client,
    task_id: str,
    reason: str,
) -> dict[str, Any]:
    redacted_reason = redact_text(reason)
    _post_event(client, task_id, "security_violation", {"reason": redacted_reason})
    _patch_status(client, task_id, "failed")
    _post_event(client, task_id, "task_failed", {"reason": redacted_reason})
    return {
        "status": "failed",
        "task_id": task_id,
        "reason": redacted_reason,
        "event": "security_violation",
    }


@celery_app.task(
    name="tasks.agent_execute",
    queue=AGENT_EXECUTE,
    max_retries=settings.TASK_MAX_RETRIES,
    autoretry_for=(Exception,),
    retry_backoff=settings.TASK_RETRY_BACKOFF,
    retry_backoff_max=settings.TASK_RETRY_BACKOFF_MAX,
    retry_jitter=settings.TASK_RETRY_JITTER,
)
def execute_task(task_id: str) -> dict[str, Any]:
    """Execute approved task in safe sandbox mode (default=fake)."""
    runner, runner_mode = _resolve_runner()

    with httpx.Client(timeout=settings.API_TIMEOUT_SECONDS) as client:
        task_resp = client.get(_task_url(task_id))
        task_resp.raise_for_status()
        task_data = task_resp.json()

        status = str(task_data.get("status", "")).lower()
        if status != "approved":
            return _fail_with_security_violation(
                client=client,
                task_id=task_id,
                reason=f"Execution blocked: task status must be approved, got '{status}'",
            )

        command = _pick_command(task_data)
        external_id = str(task_data.get("external_id") or task_id)

        try:
            validate_command(command)
            argv = _to_argv(command)
        except CommandPolicyError as exc:
            return _fail_with_security_violation(
                client=client,
                task_id=task_id,
                reason=str(exc),
            )

        worktree_path = build_worktree_path(external_id)
        try:
            safe_worktree = validate_worktree_path(worktree_path)
        except WorktreePolicyError as exc:
            return _fail_with_security_violation(
                client=client,
                task_id=task_id,
                reason=str(exc),
            )

        _patch_status(client, task_id, "running")
        _post_event(
            client,
            task_id,
            "command_started",
            {
                "command": command,
                "argv": argv,
                "worktree_path": str(safe_worktree),
                "sandbox_mode": runner_mode,
            },
        )

        try:
            result = runner.run(worktree_path=safe_worktree, command=argv, task_id=task_id)
        except SandboxTimeoutError as exc:
            redacted_error = redact_text(str(exc))
            _post_event(client, task_id, "sandbox_timeout", {"error": redacted_error})
            _patch_status(client, task_id, "failed")
            _post_event(client, task_id, "task_failed", {"reason": redacted_error})
            return {
                "status": "failed",
                "task_id": task_id,
                "event": "sandbox_timeout",
                "reason": redacted_error,
            }
        except (DockerUnavailableError, RuntimeError) as exc:
            redacted_error = redact_text(str(exc))
            _post_event(client, task_id, "sandbox_error", {"error": redacted_error})
            _patch_status(client, task_id, "failed")
            _post_event(client, task_id, "task_failed", {"reason": redacted_error})
            return {
                "status": "failed",
                "task_id": task_id,
                "event": "sandbox_error",
                "reason": redacted_error,
            }

        stdout = redact_text(result.stdout)
        stderr = redact_text(result.stderr)

        _post_event(
            client,
            task_id,
            "command_finished",
            {
                "command": command,
                "return_code": result.return_code,
                "stdout": stdout,
                "stderr": stderr,
            },
        )

        for changed in result.changed_files:
            _post_event(client, task_id, "file_changed", {"path": changed})

        if result.return_code == 0:
            _patch_status(client, task_id, "completed")
            _post_event(client, task_id, "task_completed", {"changed_files": result.changed_files})
            _patch_task_result(
                client,
                task_id,
                worktree_path=str(safe_worktree),
                result_summary=_result_summary(runner_mode=runner_mode, success=True),
                payload={
                    "execute": {
                        "command": command,
                        "return_code": result.return_code,
                        "stdout": stdout,
                        "stderr": stderr,
                        "changed_files": result.changed_files,
                        "sandbox": runner_mode,
                    }
                },
            )
            return {
                "status": "completed",
                "task_id": task_id,
                "worktree_path": str(safe_worktree),
                "command": command,
                "changed_files": result.changed_files,
            }

        _patch_status(client, task_id, "failed")
        _post_event(client, task_id, "task_failed", {"return_code": result.return_code})
        _patch_task_result(
            client,
            task_id,
            worktree_path=str(safe_worktree),
            result_summary=_result_summary(runner_mode=runner_mode, success=False),
            payload={
                "execute": {
                    "command": command,
                    "return_code": result.return_code,
                    "stdout": stdout,
                    "stderr": stderr,
                        "changed_files": result.changed_files,
                        "sandbox": runner_mode,
                    }
                },
            )
        return {
            "status": "failed",
            "task_id": task_id,
            "worktree_path": str(safe_worktree),
            "command": command,
            "stderr": stderr,
        }
