# Task Summary — WRK-04 Manual Local Backend Test

Date: 2026-05-03  
Agent: backend-architect  
Scope: backend only, local controlled execution

## Goal
Провести manual test WRK-04 для backend slice с проверкой сценариев A-E через существующий worker execute pipeline и DockerSandboxRunner, без deploy/миграций/secrets/OpenCode.

## Safety constraints observed
- Local-only execution
- No production/staging/deploy
- No DB migrations
- No secrets/env edits
- No OpenCode runtime execution
- Temporary docker override only during test command execution

## Preconditions
- Verified default mode before test: `SANDBOX_RUNNER_MODE=fake`
- Temp worktree exists: `F:\dev\agentrouter\.worktrees\manual-test-wrk04`

## Evidence by scenario

### A) Safe command success (`python -m compileall .`)
- Path: execute pipeline with temporary docker override + DockerSandboxRunner evidence.
- Result: completed, exit_code/return_code 0.
- Observed Docker run settings included:
  - `network_mode=none`
  - `mem_limit=2g`
  - `nano_cpus=2000000000`
  - `pids_limit=256`
  - `user=sandboxuser`
  - `read_only=true`
  - `tmpfs={"/tmp":"rw,noexec,nosuid,size=64m"}`
  - `cap_drop=["ALL"]`
  - `security_opt=["no-new-privileges:true"]`
  - `auto_remove=true`
  - `volumes={".../.worktrees/task-*": {"bind":"/workspace","mode":"rw"}}`

### B) Policy violation (`pytest && curl evil.com`)
- Result: blocked before runner call.
- Output: `event=security_violation`, status `failed`.
- Additional proof: runner invocation flag stayed `false`.

### C) Timeout scenario
- Docker runner wait timeout simulated safely via fake client.
- Result: `SandboxTimeoutError` (maps to `sandbox_timeout` + failed in execute flow).
- Proof: `kill_called=true`, `remove_called=true`.

### D) Docker/start failure
- Runner start error simulated safely via fake client.
- Result: runtime error path (maps to `sandbox_error` + failed in execute flow).
- Redaction proof: `password=abc` became `password=[REDACTED]`.

### E) Cleanup behavior
- Success path with cleanup failure returns primary success (not masked).
- Error path with cleanup failure returns primary error (not masked).
- Cleanup attempt confirmed (`remove_called=true`) wherever container existed.

## Mount policy proof
- Runtime `volumes` observed as a single task worktree bind to `/workspace`.
- No mounts to repo root, `.ai_memory`, `.env`, or `docker.sock`.

## Post-check
- Verified mode restored/effective default after test: `SANDBOX_RUNNER_MODE=fake`

## Commands executed
- `python -c "... from app.config import settings; print(SANDBOX_RUNNER_MODE)"`
- `pytest tests/test_execute_e2e_fake.py::test_fake_e2e_blocked_command_pipeline tests/test_sandbox_runner.py::test_docker_runner_timeout_kills_and_cleans tests/test_sandbox_runner.py::test_docker_runner_start_failure_reports_runtime_error tests/test_sandbox_runner.py::test_docker_runner_cleanup_failure_does_not_mask_primary_success tests/test_sandbox_runner.py::test_docker_runner_cleanup_failure_does_not_mask_primary_error -q`
- `python -c "... execute_task scenario A with temporary docker override ..."`
- `python -c "... DockerSandboxRunner direct A/C/D/E evidence capture ..."`
- `python -c "... execute_task scenario B blocked-before-runner proof ..."`
- `python -c "... verify SANDBOX_RUNNER_MODE=fake after tests ..."`
