# Task: CI-02 — Stabilize Pre-existing Local Validation Failures

**Date:** 2026-05-07
**Status:** PASS
**Risk:** low

---

## Objective

Fix 3 groups of pre-existing test/lint failures without touching Telegram/OpenCode/live flows.

---

## Changes

### Fix A: API pytest loop mismatch (apps/api/)

**Root cause:** API tests use `@pytest.mark.anyio` but `asyncio_mode="auto"` caused pytest-asyncio/anyio event loop mismatch. Async fixtures created on one loop, tests ran on another.

**Fix:**
1. `apps/api/pyproject.toml`: `asyncio_mode = "auto"` → `asyncio_mode = "strict"`
2. `apps/api/tests/conftest.py`: Added `anyio_backend` fixture returning `"asyncio"`
3. `apps/api/tests/test_memory_retrieval.py`: Added `@pytest.mark.anyio` to 2 async tests
4. `apps/api/tests/test_version.py`: Added `@pytest.mark.anyio` to `TestVersionEndpoint` class

**Result:** 272/272 PASS (was 162 pass / 110 fail / 7 err)

### Fix B: Worker worktree root path (apps/worker/)

**Root cause:** `worktree_policy.py` hard-coded `WORKTREE_ROOT = Path(r"F:\dev\agentrouter\.worktrees")` — Windows path breaks under WSL/Linux.

**Fix:** `apps/worker/app/services/worktree_policy.py`:
- Removed hard-coded Windows path
- `_default_worktree_root()`: walks up from file to find project root (`.git` or `apps/`), returns `root/.worktrees`
- `_resolve_worktree_root()`: uses `WORKTREE_ROOT` env var if set, else platform-safe default
- All path confinement/escape checks preserved

**Result:** 98/98 PASS (was 97/98)

### Fix C: Worker ruff celery_app.py (apps/worker/)

**Root cause:** WORKER-LINUX-01 monkey-patch had imports after module initialization (E402) and unsorted local imports (I001×2).

**Fix:** `apps/worker/app/celery_app.py`:
- Moved `os`, `sys`, `celery.apps.worker`, `close_open_fds` imports to top
- Function `_fixed_reload_current_worker()` uses top-level imports
- Monkey-patch assignment stays after `celery_app = create_celery_app()`
- SIGHUP fix behavior preserved

**Result:** 0 ruff errors (was 3)

---

## Validation Results

| Check | Before | After |
|-------|--------|-------|
| API compileall | ✅ | ✅ |
| API ruff | ✅ | ✅ |
| API pytest | 162/110/7 | **272/272** |
| Worker compileall | ✅ | ✅ |
| Worker ruff | 3 errors | **0 errors** |
| Worker pytest | 97/98 | **98/98** |
| Telegram-bot compileall | ✅ | ✅ |
| Telegram-bot ruff | ✅ | ✅ |
| Telegram-bot pytest | 75/75 | **75/75** |
| bash -n scripts | ✅ | ✅ |

---

## Changed Files

1. `apps/api/pyproject.toml` — asyncio_mode strict
2. `apps/api/tests/conftest.py` — anyio_backend fixture
3. `apps/api/tests/test_memory_retrieval.py` — @pytest.mark.anyio
4. `apps/api/tests/test_version.py` — @pytest.mark.anyio
5. `apps/worker/app/services/worktree_policy.py` — platform-safe worktree root
6. `apps/worker/app/celery_app.py` — import order fix

---

## Security

- No .env/.env.local touched
- No secrets printed
- No Telegram/OpenCode/live flows affected
- Path confinement checks preserved
