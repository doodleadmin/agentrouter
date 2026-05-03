# Task: WRK-04 manual-test hardening

| Поле | Значение |
|------|----------|
| **Task ID** | wrk-04-manual-test-hardening |
| **Date** | 2026-05-04 |
| **Agent** | backend-architect |
| **Phase** | Phase 0 — Infrastructure preparation |
| **Risk level** | medium |
| **Status** | ✅ Completed |
| **Contour** | local only; no deploy/migrations/secrets/docker |

## Context

During WRK-04 real docker smoke test, `DockerSandboxRunner.run()` was temporarily modified to accept `manual-test-*` worktree prefix alongside `task-*`. This was a temporary measure to allow the controlled smoke test using the manually-created `manual-test-wrk04` worktree. After the smoke test, this prefix needs to be restricted to prevent accidental acceptance in normal/production mode.

## Changes

### 1. `apps/worker/app/config.py`
- Added `SANDBOX_MANUAL_TEST_MODE: bool = False` — must be explicitly toggled `True` only for controlled local manual smoke tests.

### 2. `apps/worker/app/services/sandbox_runner.py`
- `DockerSandboxRunner.run()` now gates `manual-test-*` prefix behind `settings.SANDBOX_MANUAL_TEST_MODE`:
  - **Normal mode** (`SANDBOX_MANUAL_TEST_MODE=False`, default): only `task-*` prefix accepted.
  - **Manual test mode** (`SANDBOX_MANUAL_TEST_MODE=True`): `task-*` and `manual-test-*` accepted.
- Path containment check (`.worktrees` in path) is independent — always enforced regardless of mode.
- `build_worktree_path()` in `worktree_policy.py` always generates only `task-*` prefix (unchanged).

### 3. `apps/worker/tests/test_sandbox_runner.py`
- Added 5 new tests:
  - `test_rejects_manual_test_in_normal_mode` — `manual-test-*` rejected when mode=False.
  - `test_accepts_manual_test_in_test_mode` — `manual-test-*` accepted when mode=True.
  - `test_task_prefix_accepted_in_normal_mode` — `task-*` always accepted.
  - `test_task_prefix_accepted_in_test_mode` — `task-*` accepted even in test mode.
  - `test_path_traversal_still_rejected_in_test_mode` — `Path("/tmp/evil-dir")` rejected even with mode=True.

### 4. `docs/security-policy.md`
- Added WRK-04-manual-test-hardening section documenting the new gating behavior.

### 5. Memory files
- Updated `PROJECT_MEMORY.md`, `.ai_memory/current_state.md`, `.ai_memory/_INDEX.md`.
- Created this task summary.

## Verification

| Check | Result |
|-------|--------|
| `python -m compileall app` | ✅ passed |
| `ruff check app` | ✅ passed |
| `pytest tests -v` | ✅ all passed |
| `FakeSandboxRunner` is default | ✅ `SANDBOX_RUNNER_MODE=fake` |
| No real Docker run | ✅ confirmed |
| `manual-test-*` rejected in normal mode | ✅ test passes |
| `manual-test-*` accepted in test mode only | ✅ test passes |
| `task-*` prefix always accepted | ✅ existing + new tests pass |
| Path traversal always rejected | ✅ existing + new tests pass |

## Files modified

- `apps/worker/app/config.py` — added `SANDBOX_MANUAL_TEST_MODE`
- `apps/worker/app/services/sandbox_runner.py` — conditional prefix gating
- `apps/worker/tests/test_sandbox_runner.py` — 5 new hardening tests
- `docs/security-policy.md` — new section documenting the hardening
- `PROJECT_MEMORY.md` — new entry
- `.ai_memory/current_state.md` — updated status
- `.ai_memory/_INDEX.md` — updated task log count + entry

## Next steps

- WRK-04 manual-test hardening is complete.
- Next: Memory retrieval tuning (ranking quality + scope heuristics).
- Full roadmap: `docs/mvp-backlog.md`.
