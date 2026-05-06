# Task: DEV-LINUX-01C Real Stub Runtime Contour

**Date:** 2026-05-06
**Agent:** studio-orchestrator (coordinated execution)
**Contour:** local only; no deploy/migrations/.env/secrets/OpenCode

## Problem

DEV-LINUX-01 scripts passed dry-run validation but never ran against real infrastructure. Need to validate the full stub contour: DB check → API stub → Celery worker → stub runtime smoke → cleanup.

## Blockers Found & Fixed

### Blocker 1: Venv not in PATH
Scripts used `python`/`python3`/`uvicorn`/`celery` directly, expecting them in system PATH. In WSL Ubuntu, these are only in the Python 3.12 venv at `$PROJECT_ROOT/.venv/bin`.

**Fix:** Added venv auto-detection to all 8 scripts that use Python:
```bash
if [[ -d "$PROJECT_ROOT/.venv/bin" ]]; then
    export PATH="$PROJECT_ROOT/.venv/bin:$PATH"
fi
```

Scripts modified: start-api-stub.sh, start-api-opencode.sh, start-worker.sh, start-telegram-bot.sh, bootstrap-db.sh, smoke-stub-runtime.sh, smoke-real-opencode-runtime.sh, cleanup-runtime.sh.

### Blocker 2: JSON shell interpolation breaks on plan_text
Smoke scripts embedded API JSON responses via `'''$UPDATED_TASK'''` shell interpolation. The `plan_text` field contains backticks, newlines, and special characters that break bash parsing — causing `command not found` errors and silent Python failures.

**Fix:** Replaced inline shell interpolation with temp file approach:
```bash
TASK_JSON_FILE=$(mktemp)
echo "$UPDATED_TASK" > "$TASK_JSON_FILE"
python3 -c "..." "$TASK_JSON_FILE" "$EVENTS_JSON_FILE"
rm -f "$TASK_JSON_FILE" "$EVENTS_JSON_FILE"
```

### Blocker 3: Wrong events URL in smoke-real-opencode-runtime.sh
Line 241 used `$API_BASE/task-events?task_id=$TASK_ID` but actual endpoint is `$API_BASE/events/tasks/$TASK_ID/events`.

**Fix:** Corrected URL pattern.

## Real Contour Results (WSL Ubuntu 22.04)

### Environment
- Ubuntu 22.04 on WSL2 (Docker Desktop integration enabled)
- Python 3.12.13 venv at `~/agentrouter/.venv`
- PostgreSQL: `amc-dev-postgres` (pgvector:pg16, healthy)
- Redis: `amc-dev-redis` (redis:7-alpine, healthy)
- Project synced from `/mnt/f/dev/agentrouter` to `~/agentrouter`

### Step 1: check-db.sh ✅
- Container: amc-dev-postgres (running, healthy)
- pg_isready: OK
- Alembic version: `0001_initial_all_tables` (match)
- Tables: 9/9 OK (projects, agents, telegram_topics, tasks, task_events, approvals, memory_documents, memory_chunks, alembic_version)

### Step 2: start-api-stub.sh ✅
- PID: 5867
- Listen: 127.0.0.1:8000
- Provider: stub (default)
- /health: 200 OK
- /projects: 200 OK
- /agents: 200 OK

### Step 3: start-worker.sh ✅
- PID: 6316
- Celery 5.6.3
- Redis: PONG
- API: healthy
- Queues: telegram_inbound, agent_plan, agent_execute, memory_index, notifications
- Broker: redis://localhost:6379/1
- Sandbox: fake mode

### Step 4: smoke-stub-runtime.sh ✅ (ALL 8 CHECKS PASS)
- Project created: `smoke-stub-20260506-201048`
- Agent created: `smoke-agent-20260506-201048`
- Task created: `869d1ef4-452f-4b76-93e0-f3408505ea0c`
- Plan endpoint: returned in 0s (stub mode)
- **status=approved**: PASS
- **session_id=stub**: PASS
- **plan_generated=1**: PASS
- **no runtime_error**: PASS
- **no policy_blocked**: PASS
- **no command/file events**: PASS
- **no sandbox events**: PASS
- **git still clean**: PASS

### Step 5: cleanup-runtime.sh ✅
- All processes stopped (API, worker)
- Ports 8000/4096 free
- API auto-restarted in stub mode (PID 6501)
- /health, /projects, /agents: all 200 OK
- Git: clean
- PostgreSQL/Redis: kept running

## Files Modified

| File | Change |
|------|--------|
| `scripts/dev-linux/start-api-stub.sh` | +venv auto-detection |
| `scripts/dev-linux/start-api-opencode.sh` | +venv auto-detection |
| `scripts/dev-linux/start-worker.sh` | +venv auto-detection |
| `scripts/dev-linux/start-telegram-bot.sh` | +venv auto-detection |
| `scripts/dev-linux/bootstrap-db.sh` | +venv auto-detection |
| `scripts/dev-linux/smoke-stub-runtime.sh` | +venv auto-detection, +temp file JSON parsing |
| `scripts/dev-linux/smoke-real-opencode-runtime.sh` | +venv auto-detection, +temp file JSON parsing, +events URL fix |
| `scripts/dev-linux/cleanup-runtime.sh` | +venv auto-detection |

## Validation

- bash -n: 10/10 PASS
- --dry-run: 10/10 PASS (exit 0)
- --help: 10/10 PASS
- Real contour: 5/5 steps PASS
- No secrets touched, no .env modified, no Python code changed

## Key Takeaways

1. **Venv auto-detection is essential** — scripts must work without manual `source .venv/bin/activate`
2. **Never embed JSON via shell interpolation** — always use temp files or stdin piping for JSON data in bash scripts
3. **The stub runtime pipeline works end-to-end** — DB → API → stub plan → approved status → events → cleanup
4. **WSL Ubuntu 22.04 + Docker Desktop integration works** — PostgreSQL and Redis containers accessible from WSL
