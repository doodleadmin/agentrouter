# WORKER-LINUX-01: Fix Celery Worker Auto-Restart Crash on Linux

**Date:** 2026-05-06
**Status:** DONE
**Severity:** Medium (worker died after every task)

---

## Root Cause

Celery 5.6.3 installs a SIGHUP restart handler when stdout is not a TTY (i.e. `nohup`/background). The handler calls `os.execv(sys.executable, [sys.executable] + sys.argv)` to restart. When started via `python -m celery`, `sys.argv[0]` is the full path to `celery/__main__.py`. The `os.execv` restart runs it as a **standalone script** (not via `-m`), so `from . import maybe_patch_concurrency` fails with:

```
ImportError: attempted relative import with no known parent package
```

**Trigger chain:**
1. `start-worker.sh` runs `nohup python -m celery ... &` → stdout redirected to file
2. Celery detects `not self._isatty` → installs SIGHUP restart handler (overrides nohup's SIG_IGN)
3. Task completes → parent shell session exits → SIGHUP sent to process group
4. Handler fires → registers `_reload_current_worker` as atexit → sets `should_stop = EX_OK`
5. Worker exits → atexit runs `_reload_current_worker` → `os.execv(sys.argv[0])` → ImportError

**Key Celery source:** `celery/apps/worker.py`
- Line 260: `if not self._isatty:` → installs restart handler for detached processes
- Lines 469-472: `_reload_current_worker()` → `os.execv(sys.executable, [sys.executable] + sys.argv)`

---

## Fix

### 1. `apps/worker/app/celery_app.py` — Monkey-patch + SIGHUP reset

- **Monkey-patch** `_reload_current_worker` to use `python -m celery` instead of direct script path
- **Override SIGHUP** to SIG_IGN after worker init via `@worker_ready.connect` signal

### 2. `scripts/dev-linux/start-worker.sh` — `disown` after backgrounding

- Added `disown` after `nohup ... &` to prevent bash from sending SIGHUP on shell exit
- This is defense-in-depth; the Python fix handles the actual crash

---

## Changed Files

| File | Change |
|------|--------|
| `apps/worker/app/celery_app.py` | +44 lines: import signal/worker_ready, monkey-patch `_reload_current_worker`, SIGHUP→SIG_IGN handler |
| `scripts/dev-linux/start-worker.sh` | +6 lines: comment + `disown` after nohup backgrounding |

---

## Validation

| Check | Result |
|-------|--------|
| `bash -n` syntax check | PASS |
| Python syntax check | PASS |
| Worker started (PID 12165) | PASS, alive=YES |
| Task created | task-0009 (`7d2e2519`), status=created |
| Trigger plan | status=approved |
| Worker alive after 15s | PASS |
| Worker alive after 35s | PASS |
| "Restarting celery" in log | 0 occurrences |
| "ImportError" in log | 0 occurrences |
| "Traceback" in log | 0 occurrences |
| Cleanup | PASS |
| Git status | 2 files changed, +50 lines |

---

## Worker Command Before/After

**Before:**
```bash
cd "$WORKER_DIR"
nohup python -m celery -A app.celery_app worker \
    --loglevel=INFO --pool=solo --queues="$QUEUES" \
    > "$LOG_FILE" 2>&1 &
```

**After:**
```bash
cd "$WORKER_DIR"
nohup python -m celery -A app.celery_app worker \
    --loglevel=INFO --pool=solo --queues="$QUEUES" \
    > "$LOG_FILE" 2>&1 &
disown
```

Python side (celery_app.py):
```python
# Before: Celery's built-in _reload_current_worker (broken)
os.execv(sys.executable, [sys.executable] + sys.argv)

# After: Monkey-patched version
os.execv(sys.executable, [sys.executable, '-m', 'celery'] + sys.argv[1:])
```

---

## Notes

- `setsid` approach was tried first but broke PID tracking (setsid forks child when process is group leader)
- `disown` is bash-specific but script already uses `#!/usr/bin/env bash`
- The SIGHUP→SIG_IGN handler means SIGHUP restart is disabled in dev; production may want the fixed restart
- Windows side has no SIGHUP issue (signal doesn't exist on Windows)
