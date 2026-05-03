"""Tests for WRK-04 DockerSandboxRunner using fake docker client only."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.sandbox_runner import DockerSandboxRunner, SandboxTimeoutError


class _FakeContainer:
    pass


class _FakeDockerClient:
    def __init__(
        self,
        *,
        exit_code: int = 0,
        timeout: bool = False,
        start_error: Exception | None = None,
        cleanup_error: Exception | None = None,
    ) -> None:
        self.exit_code = exit_code
        self.timeout = timeout
        self.start_error = start_error
        self.cleanup_error = cleanup_error
        self.container = _FakeContainer()
        self.ran_kwargs: dict | None = None
        self.remove_called = False
        self.kill_called = False

    def run_container(self, **kwargs):
        if self.start_error is not None:
            raise self.start_error
        self.ran_kwargs = kwargs
        return self.container

    def wait_container(self, container: object, timeout: int) -> dict[str, int]:
        assert container is self.container
        if self.timeout:
            raise TimeoutError("timed out token=abc123")
        return {"StatusCode": self.exit_code}

    def logs_container(self, container: object, *, stdout: bool, stderr: bool) -> bytes:
        assert container is self.container
        if stdout:
            return b"ok token=abc123"
        if stderr:
            return b"Authorization: Bearer very-secret"
        return b""

    def remove_container(self, container: object, *, force: bool) -> None:
        assert container is self.container
        assert force is True
        self.remove_called = True
        if self.cleanup_error is not None:
            raise self.cleanup_error

    def kill_container(self, container: object) -> None:
        assert container is self.container
        self.kill_called = True


def _linux_worktree() -> Path:
    return Path("/tmp/.worktrees/task-abc12345")


def test_docker_runner_success_argv_and_security_settings() -> None:
    docker = _FakeDockerClient(exit_code=0)
    runner = DockerSandboxRunner(docker_client=docker)

    result = runner.run(
        worktree_path=_linux_worktree(),
        command=["python", "-m", "pytest"],
        task_id="task-12345678",
    )

    assert result.return_code == 0
    assert "abc123" not in result.stdout
    assert "very-secret" not in result.stderr
    assert docker.remove_called is True

    assert docker.ran_kwargs is not None
    ran = docker.ran_kwargs
    assert isinstance(ran["command"], list)
    assert ran["command"] == ["python", "-m", "pytest"]
    assert ran["working_dir"] == "/workspace"
    assert ran["network_mode"] in {"none", "internal"}
    assert ran["auto_remove"] is True
    assert ran["read_only"] is True
    assert len(ran["volumes"]) == 1
    mount_host_path = next(iter(ran["volumes"].keys()))
    assert ".worktrees" in mount_host_path.lower()
    assert "task-abc12345" in mount_host_path.lower()
    assert ran["volumes"][mount_host_path]["bind"] == "/workspace"
    assert ran["volumes"][mount_host_path]["mode"] == "rw"
    assert "docker.sock" not in str(ran["volumes"])


def test_docker_runner_non_zero_exit() -> None:
    docker = _FakeDockerClient(exit_code=2)
    runner = DockerSandboxRunner(docker_client=docker)

    result = runner.run(worktree_path=_linux_worktree(), command=["pytest"], task_id="task-z")
    assert result.return_code == 2
    assert docker.remove_called is True


def test_docker_runner_timeout_kills_and_cleans() -> None:
    docker = _FakeDockerClient(timeout=True)
    runner = DockerSandboxRunner(docker_client=docker)

    with pytest.raises(SandboxTimeoutError):
        runner.run(worktree_path=_linux_worktree(), command=["pytest"], task_id="task-t")

    assert docker.kill_called is True
    assert docker.remove_called is True


def test_docker_runner_start_failure_reports_runtime_error() -> None:
    docker = _FakeDockerClient(start_error=RuntimeError("cannot start password=abc"))
    runner = DockerSandboxRunner(docker_client=docker)

    with pytest.raises(RuntimeError, match="Docker sandbox error") as exc_info:
        runner.run(worktree_path=_linux_worktree(), command=["pytest"], task_id="task-e")

    assert "abc" not in str(exc_info.value)


def test_docker_runner_rejects_non_task_worktree() -> None:
    docker = _FakeDockerClient()
    runner = DockerSandboxRunner(docker_client=docker)

    with pytest.raises(ValueError, match="Invalid task worktree mount path"):
        runner.run(worktree_path=Path("/tmp/.worktrees/random-dir"), command=["pytest"], task_id="task-r")


def test_docker_runner_cleanup_failure_does_not_mask_primary_success() -> None:
    docker = _FakeDockerClient(exit_code=0, cleanup_error=RuntimeError("cleanup boom"))
    runner = DockerSandboxRunner(docker_client=docker)

    result = runner.run(worktree_path=_linux_worktree(), command=["pytest"], task_id="task-clean-ok")

    assert result.return_code == 0
    assert docker.remove_called is True


def test_docker_runner_cleanup_failure_does_not_mask_primary_error() -> None:
    docker = _FakeDockerClient(
        start_error=RuntimeError("cannot start password=abc"),
        cleanup_error=RuntimeError("cleanup boom"),
    )
    runner = DockerSandboxRunner(docker_client=docker)

    with pytest.raises(RuntimeError, match="Docker sandbox error") as exc_info:
        runner.run(worktree_path=_linux_worktree(), command=["pytest"], task_id="task-clean-err")

    assert "abc" not in str(exc_info.value)


# ── WRK-04 manual-test prefix hardening ────────────────────────────────


def _manual_test_worktree() -> Path:
    return Path("/tmp/.worktrees/manual-test-wrk04")


def test_rejects_manual_test_in_normal_mode() -> None:
    """manual-test-* worktree prefix MUST be rejected when SANDBOX_MANUAL_TEST_MODE=False."""
    docker = _FakeDockerClient()
    runner = DockerSandboxRunner(docker_client=docker)

    with patch("app.services.sandbox_runner.settings") as mock_settings:
        mock_settings.SANDBOX_MANUAL_TEST_MODE = False
        with pytest.raises(ValueError, match="Invalid task worktree mount path"):
            runner.run(
                worktree_path=_manual_test_worktree(),
                command=["pytest"],
                task_id="task-manual-bad",
            )


def test_accepts_manual_test_in_test_mode() -> None:
    """manual-test-* worktree prefix MUST be accepted when SANDBOX_MANUAL_TEST_MODE=True."""
    docker = _FakeDockerClient(exit_code=0)
    runner = DockerSandboxRunner(docker_client=docker)

    with patch("app.services.sandbox_runner.settings") as mock_settings:
        mock_settings.SANDBOX_MANUAL_TEST_MODE = True
        result = runner.run(
            worktree_path=_manual_test_worktree(),
            command=["python", "-m", "compileall", "."],
            task_id="task-manual-ok",
        )

    assert result.return_code == 0
    assert docker.remove_called is True
    # Verify mount path contains manual-test prefix
    assert docker.ran_kwargs is not None
    mount_host_path = next(iter(docker.ran_kwargs["volumes"].keys()))
    assert "manual-test-wrk04" in mount_host_path


def test_task_prefix_accepted_in_normal_mode() -> None:
    """task-* worktree prefix MUST always be accepted (normal mode)."""
    docker = _FakeDockerClient(exit_code=0)
    runner = DockerSandboxRunner(docker_client=docker)

    with patch("app.services.sandbox_runner.settings") as mock_settings:
        mock_settings.SANDBOX_MANUAL_TEST_MODE = False
        result = runner.run(
            worktree_path=_linux_worktree(),
            command=["ruff", "check", "."],
            task_id="task-normal-ok",
        )

    assert result.return_code == 0
    assert docker.remove_called is True


def test_task_prefix_accepted_in_test_mode() -> None:
    """task-* worktree prefix MUST also be accepted when SANDBOX_MANUAL_TEST_MODE=True."""
    docker = _FakeDockerClient(exit_code=0)
    runner = DockerSandboxRunner(docker_client=docker)

    with patch("app.services.sandbox_runner.settings") as mock_settings:
        mock_settings.SANDBOX_MANUAL_TEST_MODE = True
        result = runner.run(
            worktree_path=_linux_worktree(),
            command=["pytest", "tests"],
            task_id="task-test-mode",
        )

    assert result.return_code == 0
    assert docker.remove_called is True


def test_path_traversal_still_rejected_in_test_mode() -> None:
    """Path traversal (no .worktrees in path) MUST be rejected even in manual test mode."""
    docker = _FakeDockerClient()
    runner = DockerSandboxRunner(docker_client=docker)

    with patch("app.services.sandbox_runner.settings") as mock_settings:
        mock_settings.SANDBOX_MANUAL_TEST_MODE = True
        with pytest.raises(ValueError, match="Invalid task worktree mount path"):
            runner.run(
                worktree_path=Path("/tmp/evil-dir"),
                command=["pytest"],
                task_id="task-traversal",
            )
