# Runtime Runbook — Agent Mission Control

> **BE-11:** Local dev pipeline automation. PowerShell scripts for consistent, auditable runtime smoke testing.
> **Status:** Complete — 9 scripts, all parse-validated, all support `-DryRun`.

---

## Quick Start

```powershell
# 1. Ensure Docker daemon is running, then start infrastructure
docker compose -f infra/docker/docker-compose.yml up -d

# 2. Wait for healthy containers, then verify
.\scripts\dev\check-db.ps1

# 3. Bootstrap database (skip if tables already exist)
.\scripts\dev\bootstrap-db.ps1

# 4. Start API in stub mode
.\scripts\dev\start-api-stub.ps1

# At this point, the API is running on http://127.0.0.1:8000 with stub runtime.
# Proceed to smoke tests or real OpenCode workflow as needed.
```

## Full Pipeline

| Step | Script | Description | Preconditions | Output |
|------|--------|-------------|---------------|--------|
| 1 | `docker compose up -d` | Start postgres + redis | Docker daemon running | Healthy containers |
| 2 | `check-db.ps1` | Verify DB health: container state, pg_isready, 9 tables, alembic version | Postgres container running | PASS/FAIL report (supports `-Json`) |
| 3 | `bootstrap-db.ps1` | Apply `alembic upgrade head` | Postgres healthy, alembic installed | Migration applied (skips if tables exist) |
| 4a | `start-api-stub.ps1` | Start API with `RUNTIME_PROVIDER=stub` | DB bootstrapped, uvicorn installed | API on `127.0.0.1:8000` |
| 4b | `start-opencode.ps1` | Start OpenCode server | `opencode` launcher available | OpenCode on `127.0.0.1:4096` |
| 4c | `start-api-opencode.ps1` | Start API with `opencode_http` provider | OpenCode healthy at `127.0.0.1:4096` | API on `127.0.0.1:8000` (real runtime) |
| 5 | `start-worker.ps1` | Start Celery worker | Redis healthy, API `/health`=200 | Worker consuming queues |
| 6a | `smoke-stub-runtime.ps1` | Stub smoke test (plan-only) | API in stub mode, git clean | 9 verification checks |
| 6b | `smoke-real-opencode-runtime.ps1` | Real OpenCode smoke test | API in opencode_http mode, OpenCode healthy, git clean | 13 verification checks |
| 7 | `cleanup-runtime.ps1` | Stop OpenCode/Celery/API, auto-restart stub | — | API back in stub mode, env cleaned |

## Dependencies Diagram

```
                  ┌─────────────┐
                  │ docker daemon│
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │ compose up  │  (postgres + redis)
                  └──────┬──────┘
                         │
              ┌──────────┼──────────┐
              │                     │
       ┌──────▼──────┐       ┌──────▼──────┐
       │ check-db    │       │ redis (PONG)│
       └──────┬──────┘       └──────┬──────┘
              │                     │
       ┌──────▼──────┐              │
       │ bootstrap-db│              │
       └──────┬──────┘              │
              │                     │
    ┌─────────┼─────────────────────┼─────────┐
    │         │                     │         │
┌───▼───┐ ┌───▼────────┐  ┌────────▼──────┐  │
│start  │ │start-      │  │start-opencode │  │
│api-   │ │api-        │  │  (port 4096)  │  │
│stub   │ │opencode ◄──┼──┤ 127.0.0.1     │  │
│(stub) │ │(opencode_http)│              │  │
└───┬───┘ └───┬────────┘  └──────────────┘  │
    │         │                              │
    │    ┌────▼────┐                    ┌────▼────┐
    │    │smoke    │                    │start-   │
    │    │real-    │                    │worker   │
    │    │opencode │                    └─────────┘
    │    └─────────┘
    │
┌───▼───┐
│smoke  │
│stub-  │
│runtime│
└───┬───┘
    │
┌───▼───────┐
│cleanup-   │
│runtime    │
│(stops all,│
│restart    │
│stub API)  │
└───────────┘
```

## Stub Smoke vs Real OpenCode Smoke

### Stub Smoke (`smoke-stub-runtime.ps1`)

- **Purpose:** Validate stub runtime provider wiring (no OpenCode server needed)
- **Prerequisites:** API in `RUNTIME_PROVIDER=stub`, git clean
- **What it does:**
  1. Creates project + agent + low-risk task via API
  2. Calls `POST /runtime/tasks/{id}/plan` directly (bypassing Celery worker)
  3. Verifies: status=approved, session_id=stub-session, plan_generated=1
  4. Verifies: NO runtime_error, policy_blocked, command/file/sandbox events
  5. Verifies: git stays clean
- **Timeout:** 120s for plan generation
- **Exit code:** 0 on all checks pass, 1 on any failure

### Real OpenCode Smoke (`smoke-real-opencode-runtime.ps1`)

- **Purpose:** End-to-end validation with real OpenCode 1.14.33 server
- **Prerequisites:** API in `opencode_http` mode, OpenCode healthy at `127.0.0.1:4096`, git clean
- **What it does:**
  1. Creates project + agent + low-risk task via API
  2. Routes task through status: created → routed → planning
  3. Calls `POST /runtime/tasks/{id}/plan` directly (bypassing Celery worker)
  4. Verifies: status=approved, session_id starts with `ses_`, plan_generated=1
  5. Verifies: no stub fingerprints in plan_text (5 patterns checked)
  6. Verifies: `runtime_session_created` BEFORE `runtime_event_received` (P2-5 ordering)
  7. Verifies: no runtime_error, runtime_timeout, policy_blocked
  8. Verifies: no command_started, command_finished, file_changed, sandbox events
  9. Verifies: no reasoning leak in plan_text (3 patterns)
  10. Verifies: no secret leak in plan_text (4 secret patterns)
  11. Verifies: git stays clean
  12. Shows plan preview (first 300 chars)
- **Timeout:** 360s default (configurable via `-TimeoutSeconds`)
- **Exit code:** 0 on all checks pass, 1 on any failure

## Cleanup Procedure

```powershell
# Full cleanup: stop OpenCode, Celery, API → auto-restart API in stub mode
.\scripts\dev\cleanup-runtime.ps1

# Skip auto-restart (keep everything stopped)
.\scripts\dev\cleanup-runtime.ps1 -SkipApiRestart

# Dry-run (see what would happen)
.\scripts\dev\cleanup-runtime.ps1 -DryRun
```

Cleanup **never** stops postgres/redis containers. DB data is preserved across smoke test cycles.

## Script Reference

All scripts in `scripts/dev/`:

| Script | Lines | Params | Purpose |
|--------|-------|--------|---------|
| `check-db.ps1` | 230 | `-Json`, `-DryRun` | DB health check |
| `bootstrap-db.ps1` | 197 | `-Force`, `-DryRun` | Alembic migration |
| `start-api-stub.ps1` | 188 | `-Port`, `-NoReload`, `-DryRun` | Start stub API |
| `start-opencode.ps1` | 200 | `-Port`, `-DryRun` | Start OpenCode server |
| `start-api-opencode.ps1` | 235 | `-Port`, `-OpenCodeUrl`, `-DryRun` | Start real-runtime API |
| `start-worker.ps1` | 153 | `-Concurrency`, `-Queues`, `-ApiTimeout`, `-DryRun` | Start Celery worker |
| `smoke-stub-runtime.ps1` | 335 | `-DryRun` | Stub smoke test |
| `smoke-real-opencode-runtime.ps1` | 406 | `-TimeoutSeconds`, `-DryRun` | Real OpenCode smoke test |
| `cleanup-runtime.ps1` | 267 | `-Port`, `-OpenCodePort`, `-SkipApiRestart`, `-DryRun` | Cleanup + auto-restart stub |

**Total:** 9 scripts, 1934 lines.

## Safety Rules Summary

### Binding & Network

- All services bind to `127.0.0.1` only — **never** `0.0.0.0`
- API on port 8000 (configurable)
- OpenCode on port 4096 (configurable)
- Port 3001 is **forbidden** (excluded from all scripts)

### Environment

- **No `.env` file writes** — ever
- All runtime overrides are **process-scoped** (`$env:VARIABLE` in PowerShell session only)
- `DATABASE_URL` is set process-scoped in `bootstrap-db.ps1` and removed in `finally` block
- `start-api-stub.ps1` explicitly removes all RUNTIME_* env vars before starting
- `cleanup-runtime.ps1` removes all RUNTIME_* env vars

### Secrets

- No secrets, tokens, or credentials in any script
- `start-opencode.ps1` explicitly removes `OPENCODE_SERVER_PASSWORD`/`OPENCODE_SERVER_USERNAME` from child process env

### Production Safety

- No production/staging targets
- No deploy commands
- No database DROP/TRUNCATE/DELETE
- `bootstrap-db.ps1` guard: skips if tables exist (unless `-Force` with explicit `agent_mc` confirmation)

## Worker Bypass Note

**All smoke test scripts use direct `POST /runtime` API calls** — they do **not** go through the Celery worker.

This is intentional:
- Smokes validate the API-to-OpenCode transport chain directly
- Celery worker is tested separately via `start-worker.ps1`
- The `start-worker.ps1` script is available for worker-integrated testing

The scripts print a prominent notice when bypassing the worker:
```
**************************************************
* Worker bypass: direct POST /runtime used.      *
**************************************************
```

## Troubleshooting

### `check-db.ps1` fails: container not healthy
```powershell
docker compose -f infra/docker/docker-compose.yml ps
docker compose -f infra/docker/docker-compose.yml logs postgres
```

### `bootstrap-db.ps1` fails: alembic not installed
```powershell
pip install alembic asyncpg
```

### `start-opencode.ps1` fails: launcher not found
- OpenCode must be installed: either via `npm install -g @opencode/cli` or available in `%APPDATA%\npm\opencode.cmd`
- Check: `opencode --version`

### `start-api-opencode.ps1` fails: config validation
- Ensure `RUNTIME_ALLOW_REAL_OPENCODE_HTTP=true` is set
- Ensure `OPENCODE_SERVER_URL` points to a healthy OpenCode server
- Check: `Invoke-RestMethod http://127.0.0.1:4096/global/health`

### `smoke-real-opencode-runtime.ps1` fails: plan timeout
- Default timeout is 360s — increase with `-TimeoutSeconds 600`
- OpenCode 1.14.33 may take 80–170s for plan generation
- Check API logs for `runtime_retry_scheduled` events

### `smoke-stub-runtime.ps1` fails: status not approved
- Ensure API is in stub mode: `RUNTIME_PROVIDER=stub`
- Check that task was created with `risk_level=low` (auto-approve)
- Check events at `GET /task-events?task_id=<id>`

### Port conflict
```powershell
# Find what's on port 8000
Get-NetTCPConnection -LocalPort 8000 -LocalAddress "127.0.0.1"
# Or use cleanup which auto-handles stale processes
.\scripts\dev\cleanup-runtime.ps1 -SkipApiRestart
```

### Git dirty before smoke
Smoke tests require clean git working tree. Commit or stash changes:
```powershell
git stash
# ... run smoke ...
git stash pop
```

## Dry-Run Mode

All 9 scripts support `-DryRun` parameter for safe pre-flight validation:

```powershell
.\scripts\dev\check-db.ps1 -DryRun
.\scripts\dev\bootstrap-db.ps1 -DryRun
.\scripts\dev\start-api-stub.ps1 -DryRun
.\scripts\dev\start-opencode.ps1 -DryRun
.\scripts\dev\start-api-opencode.ps1 -DryRun
.\scripts\dev\start-worker.ps1 -DryRun
.\scripts\dev\smoke-stub-runtime.ps1 -DryRun
.\scripts\dev\smoke-real-opencode-runtime.ps1 -DryRun
.\scripts\dev\cleanup-runtime.ps1 -DryRun
```

Dry-run mode validates preconditions, prints would-do actions, and exits 0 — no services are started, no API calls made, no state modified.

---

## References

- [Smoke Test Procedure (manual)](smoke-test-opencode.md)
- [Security Policy (+BE-11 Safety Rules)](security-policy.md)
- [Architecture Overview](architecture.md)
- [MVP Backlog](mvp-backlog.md)
