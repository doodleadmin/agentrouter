from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.config import settings
from app.services.redaction import redact_text
from app.services.sandbox_runner import DockerSandboxRunner


@dataclass
class ContainerRef:
    container_id: str
    name: str


class CliDockerClient:
    def __init__(self) -> None:
        self.last_run_kwargs = None
        self.last_container_id = None
        self.last_inspect = None
        self.cleanup_attempted = False
        self.cleanup_completed = False

    def _run(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(args, check=True, capture_output=True, text=True)

    def run_container(self, **kwargs):
        self.last_run_kwargs = kwargs
        args = [
            "docker",
            "run",
            "-d",
            "--rm",
            "--name",
            kwargs["name"],
            "--workdir",
            kwargs["working_dir"],
            "--network",
            kwargs["network_mode"],
            "--memory",
            kwargs["mem_limit"],
            "--cpus",
            f"{kwargs['nano_cpus'] / 1_000_000_000:.3f}",
            "--pids-limit",
            str(kwargs["pids_limit"]),
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            "--user",
            kwargs["user"],
            "--security-opt",
            kwargs["security_opt"][0],
            "--cap-drop",
            kwargs["cap_drop"][0],
        ]

        for host_path, mount in kwargs["volumes"].items():
            args.extend(["-v", f"{host_path}:{mount['bind']}:{mount['mode']}"])

        args.append(kwargs["image"])
        args.extend(kwargs["command"])

        result = self._run(args)
        container_id = result.stdout.strip()
        self.last_container_id = container_id

        inspect = self._run(["docker", "inspect", container_id])
        self.last_inspect = json.loads(inspect.stdout)[0]

        return ContainerRef(container_id=container_id, name=kwargs["name"])

    def wait_container(self, container: object, timeout: int) -> dict[str, int]:
        assert isinstance(container, ContainerRef)
        result = self._run(["docker", "wait", container.container_id])
        return {"StatusCode": int(result.stdout.strip() or "1")}

    def logs_container(self, container: object, *, stdout: bool, stderr: bool) -> bytes:
        assert isinstance(container, ContainerRef)
        args = ["docker", "logs"]
        if stdout and not stderr:
            args.append("--stdout")
        if stderr and not stdout:
            args.append("--stderr")
        args.append(container.container_id)
        result = subprocess.run(args, check=False, capture_output=True)
        if stdout and not stderr:
            return result.stdout
        if stderr and not stdout:
            return result.stderr
        return result.stdout + result.stderr

    def remove_container(self, container: object, *, force: bool) -> None:
        assert isinstance(container, ContainerRef)
        self.cleanup_attempted = True
        result = subprocess.run(
            ["docker", "rm", "-f", container.container_id],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 or "No such container" in (result.stderr or ""):
            self.cleanup_completed = True

    def kill_container(self, container: object) -> None:
        assert isinstance(container, ContainerRef)
        subprocess.run(["docker", "kill", container.container_id], check=False, capture_output=True)


def main() -> None:
    target_worktree = Path(r"F:\dev\agentrouter\.worktrees\manual-test-wrk04")
    default_mode = settings.SANDBOX_RUNNER_MODE

    cli_client = CliDockerClient()
    runner = DockerSandboxRunner(docker_client=cli_client)

    result = runner.run(
        worktree_path=target_worktree,
        command=["python", "-m", "compileall", "."],
        task_id="task-wrk04-real-smoke",
    )

    inspect = cli_client.last_inspect or {}
    mounts = inspect.get("Mounts", [])
    host_mounts = [m.get("Source", "") for m in mounts]

    output = {
        "default_mode_before": default_mode,
        "effective_mode_for_invocation": "docker (direct DockerSandboxRunner invocation)",
        "effective_image": settings.DOCKER_SANDBOX_IMAGE,
        "effective_network_mode": settings.DOCKER_SANDBOX_NETWORK_MODE,
        "container_started": cli_client.last_container_id is not None,
        "container_id": cli_client.last_container_id,
        "command": ["python", "-m", "compileall", "."],
        "exit_code": result.return_code,
        "stdout_redaction_path_applied": result.stdout == redact_text(result.stdout),
        "stderr_redaction_path_applied": result.stderr == redact_text(result.stderr),
        "cleanup_attempted": cli_client.cleanup_attempted,
        "cleanup_completed": cli_client.cleanup_completed,
        "runner_volumes": cli_client.last_run_kwargs.get("volumes") if cli_client.last_run_kwargs else None,
        "runner_settings": {
            "working_dir": cli_client.last_run_kwargs.get("working_dir") if cli_client.last_run_kwargs else None,
            "network_mode": cli_client.last_run_kwargs.get("network_mode") if cli_client.last_run_kwargs else None,
            "mem_limit": cli_client.last_run_kwargs.get("mem_limit") if cli_client.last_run_kwargs else None,
            "nano_cpus": cli_client.last_run_kwargs.get("nano_cpus") if cli_client.last_run_kwargs else None,
            "pids_limit": cli_client.last_run_kwargs.get("pids_limit") if cli_client.last_run_kwargs else None,
            "read_only": cli_client.last_run_kwargs.get("read_only") if cli_client.last_run_kwargs else None,
            "tmpfs": cli_client.last_run_kwargs.get("tmpfs") if cli_client.last_run_kwargs else None,
            "user": cli_client.last_run_kwargs.get("user") if cli_client.last_run_kwargs else None,
            "security_opt": cli_client.last_run_kwargs.get("security_opt") if cli_client.last_run_kwargs else None,
            "cap_drop": cli_client.last_run_kwargs.get("cap_drop") if cli_client.last_run_kwargs else None,
            "auto_remove": cli_client.last_run_kwargs.get("auto_remove") if cli_client.last_run_kwargs else None,
        },
        "inspect_mounts": mounts,
        "forbidden_mounts_present": {
            "repo_root": any(p.replace('\\\\', '/').lower().rstrip('/') == 'f:/dev/agentrouter' for p in host_mounts),
            ".env": any(p.lower().endswith('/.env') or p.lower().endswith('\\\\.env') for p in host_mounts),
            ".ai_memory": any('.ai_memory' in p.lower() for p in host_mounts),
            "docker_sock": any('docker.sock' in p.lower() for p in host_mounts),
        },
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
