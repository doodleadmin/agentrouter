"""Sandbox execution abstraction for WRK-04.

Supports:
- FakeSandboxRunner (default mode)
- DockerSandboxRunner (opt-in mode via config)

DockerSandboxRunner is implemented with an injectable client protocol so tests
can run with fake docker clients and without real Docker runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.config import settings
from app.services.redaction import redact_text


@dataclass
class SandboxResult:
    return_code: int
    stdout: str
    stderr: str
    changed_files: list[str]


class SandboxRunner(Protocol):
    def run(self, *, worktree_path: Path, command: list[str], task_id: str | None = None) -> SandboxResult:
        """Execute command in sandbox and return structured result."""


class FakeSandboxRunner:
    """Deterministic fake runner for tests/no-op execution."""

    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def run(self, *, worktree_path: Path, command: list[str], task_id: str | None = None) -> SandboxResult:
        joined = " ".join(command)
        if self.should_fail:
            return SandboxResult(
                return_code=1,
                stdout="",
                stderr=f"simulated failure for command: {joined}",
                changed_files=[],
            )
        return SandboxResult(
            return_code=0,
            stdout=f"simulated success in {worktree_path}\ncommand={joined}",
            stderr="",
            changed_files=["apps/api/app/main.py"],
        )


class DockerUnavailableError(RuntimeError):
    """Raised when Docker SDK/runtime is unavailable."""


class SandboxTimeoutError(RuntimeError):
    """Raised when sandbox execution exceeds timeout."""


class DockerClientProtocol(Protocol):
    """Minimal docker client protocol used by DockerSandboxRunner."""

    def run_container(
        self,
        *,
        image: str,
        command: list[str],
        volumes: dict[str, dict[str, str]],
        working_dir: str,
        network_mode: str,
        mem_limit: str,
        nano_cpus: int,
        pids_limit: int,
        read_only: bool,
        tmpfs: dict[str, str],
        user: str,
        security_opt: list[str],
        cap_drop: list[str],
        auto_remove: bool,
        detach: bool,
        name: str,
    ) -> object:
        ...

    def wait_container(self, container: object, timeout: int) -> dict[str, int]:
        ...

    def logs_container(self, container: object, *, stdout: bool, stderr: bool) -> bytes:
        ...

    def remove_container(self, container: object, *, force: bool) -> None:
        ...

    def kill_container(self, container: object) -> None:
        ...


class DockerSandboxRunner:
    """Docker-backed sandbox runner (opt-in).

    Security constraints:
    - command is argv list only (no shell strings)
    - mounts only validated task worktree to /workspace
    - no env forwarding
    - default network mode blocks external access (none)
    - cleanup always attempted in finally
    """

    def __init__(self, *, docker_client: DockerClientProtocol | None = None) -> None:
        self._docker_client = docker_client

    @staticmethod
    def _make_container_name(task_id: str | None) -> str:
        seed = (task_id or "task").replace("_", "-")
        safe = "".join(ch for ch in seed.lower() if ch.isalnum() or ch == "-")
        safe = safe.strip("-") or "task"
        return f"amc-sandbox-{safe[:24]}"

    def _get_client(self) -> DockerClientProtocol:
        if self._docker_client is not None:
            return self._docker_client
        try:
            import docker  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on environment
            raise DockerUnavailableError("Docker SDK is unavailable") from exc

        sdk_client = docker.from_env()

        class _SdkAdapter:
            def run_container(self, **kwargs):
                return sdk_client.containers.run(**kwargs)

            def wait_container(self, container: object, timeout: int) -> dict[str, int]:
                return container.wait(timeout=timeout)

            def logs_container(self, container: object, *, stdout: bool, stderr: bool) -> bytes:
                return container.logs(stdout=stdout, stderr=stderr)

            def remove_container(self, container: object, *, force: bool) -> None:
                container.remove(force=force)

            def kill_container(self, container: object) -> None:
                container.kill()

        return _SdkAdapter()

    def run(self, *, worktree_path: Path, command: list[str], task_id: str | None = None) -> SandboxResult:
        if not command:
            raise ValueError(redact_text("Empty argv command"))

        safe_worktree = worktree_path.resolve()
        parts_lower = [p.lower() for p in safe_worktree.parts]
        valid_prefixes: tuple[str, ...] = ("task-",)
        if settings.SANDBOX_MANUAL_TEST_MODE:
            valid_prefixes = ("task-", "manual-test-")
        if ".worktrees" not in parts_lower or not safe_worktree.name.startswith(valid_prefixes):
            raise ValueError(redact_text(f"Invalid task worktree mount path: {safe_worktree}"))

        client = self._get_client()
        container: object | None = None
        container_name = self._make_container_name(task_id)

        # Windows path caveat for Docker Desktop; for MVP we enforce Linux worker host
        # for real SDK mode. Injected fake clients in tests are allowed.
        if safe_worktree.drive and self._docker_client is None:
            raise DockerUnavailableError(
                redact_text(
                    "DockerSandboxRunner MVP supports Linux worker host paths only"
                )
            )

        volumes = {
            str(safe_worktree): {
                "bind": "/workspace",
                "mode": "rw",
            }
        }

        try:
            container = client.run_container(
                image=settings.DOCKER_SANDBOX_IMAGE,
                command=command,
                volumes=volumes,
                working_dir="/workspace",
                network_mode=settings.DOCKER_SANDBOX_NETWORK_MODE,
                mem_limit=settings.DOCKER_SANDBOX_MEMORY_LIMIT,
                nano_cpus=int(settings.DOCKER_SANDBOX_CPU_LIMIT * 1_000_000_000),
                pids_limit=settings.DOCKER_SANDBOX_PIDS_LIMIT,
                read_only=True,
                tmpfs={"/tmp": "rw,noexec,nosuid,size=64m"},
                user="sandboxuser",
                security_opt=["no-new-privileges:true"],
                cap_drop=["ALL"],
                auto_remove=True,
                detach=True,
                name=container_name,
            )

            try:
                wait_result = client.wait_container(
                    container,
                    timeout=settings.DOCKER_SANDBOX_TIMEOUT_SECONDS,
                )
            except TimeoutError as exc:
                try:
                    client.kill_container(container)
                except Exception:
                    pass
                raise SandboxTimeoutError(redact_text(str(exc))) from exc

            return_code = int(wait_result.get("StatusCode", 1))
            stdout = redact_text(client.logs_container(container, stdout=True, stderr=False).decode("utf-8", errors="replace"))
            stderr = redact_text(client.logs_container(container, stdout=False, stderr=True).decode("utf-8", errors="replace"))

            return SandboxResult(
                return_code=return_code,
                stdout=stdout,
                stderr=stderr,
                changed_files=[],
            )
        except SandboxTimeoutError:
            raise
        except DockerUnavailableError:
            raise
        except Exception as exc:
            raise RuntimeError(redact_text(f"Docker sandbox error: {exc}")) from exc
        finally:
            if container is not None:
                try:
                    client.remove_container(container, force=True)
                except Exception:
                    # Cleanup best-effort; execution result already determined.
                    pass
