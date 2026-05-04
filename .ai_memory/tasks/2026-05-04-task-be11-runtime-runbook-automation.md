# Task Log: BE-11 Runtime Runbook + Local Smoke Automation

**Date:** 2026-05-04
**Agent:** devops-automator + knowledge-steward
**Goal:** Create 9 PowerShell scripts + runbook documentation for local dev pipeline automation
**Status:** COMPLETE

---

## Summary

Created a complete local dev pipeline automation suite with 9 PowerShell scripts (1934 lines total) and comprehensive documentation including a main runbook, safety rules, and updated memory files.

## Changed Files

### Scripts Created (9 files, `scripts/dev/`)

| # | File | Lines | Purpose |
|---|------|-------|---------|
| 1 | `check-db.ps1` | 230 | DB health check: container state, pg_isready, 9 tables, alembic version. Supports `-Json` and `-DryRun`. |
| 2 | `bootstrap-db.ps1` | 197 | Alembic `upgrade head` with guard. Skips if tables exist (unless `-Force` with explicit `agent_mc` confirmation). Process-scoped `DATABASE_URL` only. |
| 3 | `start-api-stub.ps1` | 188 | Start uvicorn with `RUNTIME_PROVIDER=stub` on `127.0.0.1:8000`. Removes any existing RUNTIME overrides. Verifies `/health`, `/projects`, `/agents`. |
| 4 | `start-opencode.ps1` | 200 | Dynamic OpenCode launcher (npm cmd → PATH exe). Kills stale processes on port 4096. Verifies `/global/health`, `/doc`, binds to 127.0.0.1 only. Strips auth env vars. |
| 5 | `start-api-opencode.ps1` | 235 | Start API with `opencode_http` provider. Stops existing API on target port. Sets process-scoped `RUNTIME_PROVIDER`, `OPENCODE_SERVER_URL`, `RUNTIME_ALLOW_REAL_OPENCODE_HTTP`, `DEBUG`. Validates config via `python -c` assert before start. Never sets `DATABASE_URL`. |
| 6 | `start-worker.ps1` | 153 | Start Celery worker. Verifies Redis `PONG` and API `/health=200`. Sets process-scoped `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `API_BASE_URL`, `API_TIMEOUT_SECONDS`. |
| 7 | `smoke-stub-runtime.ps1` | 335 | Stub provider smoke test. Create project → agent → low-risk task → `POST /runtime/plan` (worker bypass). 9 verification checks: status=approved, session_id=stub-session, plan_generated=1, no errors/policy blocks/command/file/sandbox events, git clean. |
| 8 | `smoke-real-opencode-runtime.ps1` | 406 | Real OpenCode E2E smoke test. 13 verification checks: status approved, session_id starts with `ses_`, no stub fingerprints (5 patterns), event ordering (create < recv), plan_generated=1, no runtime_error/timeout/policy_blocked, no command/file/sandbox events, no reasoning leak (3 patterns), no secret leak (4 patterns), git clean. Plan preview shown. |
| 9 | `cleanup-runtime.ps1` | 267 | Stop OpenCode (port 4096), Celery worker, API (port 8000). Wait for ports to free. Remove all RUNTIME_* env vars. Auto-restart API in stub mode. Verify ports free, git clean. Never stops postgres/redis. |

### Documentation Created

- **`docs/runtime-runbook.md`** — Full runbook covering:
  - Quick start (docker compose up → check-db → bootstrap-db → start-api-stub)
  - Full pipeline table (9 steps with scripts, preconditions, outputs)
  - ASCII dependencies diagram
  - Stub smoke vs real OpenCode smoke workflows (detailed)
  - Cleanup procedure with all options
  - Reference table for all 9 scripts (lines, params, purpose)
  - Safety rules summary (binding, env, secrets, production safety)
  - Worker bypass note (with prominent notice explanation)
  - Troubleshooting section (7 common issues with solutions)
  - Dry-run mode documentation

### Documentation Updated

- **`docs/smoke-test-opencode.md`** — Added "Automated Alternative (BE-11)" section at top referencing all 6 relevant scripts with a comparison table. Existing manual procedure preserved below.
- **`docs/security-policy.md`** — Added "BE-11: Runtime Runbook Safety Rules" section with:
  - Forbidden operations (F1-F10): no .env writes, no persistent env, no prod/staging, no deploy, no destructive DB, no 0.0.0.0, no port 3001, no mutating tools, no credential logging, no DATABASE_URL persistence
  - Abort criteria (A1-A13): git dirty, wrong bind, /projects=500, .env mutation, stub fingerprints, reasoning leak, runtime_error/timeout, policy_blocked, command/sandbox events
  - Pre-smoke checklist (P1-P15): docker, compose, postgres, redis, tables, alembic, git, env, runtime provider, sandbox mode, ports, Python packages
  - Post-smoke checklist (T1-T12): git clean, .env, API stub mode, env vars removed, port free, artifacts cleaned, processes, containers, secrets review
  - Secrets handling (S1-S8): no .env writes, no persistent secrets, auth stripping, pattern scanning, credential-free source code, process-scoped DATABASE_URL
  - Worker bypass safety rationale

### Memory Files Updated

- **`PROJECT_MEMORY.md`** — Status line updated to include BE-11; New BE-11 section under "Изменения" (lines 695-709 replaced with comprehensive summary)
- **`.ai_memory/current_state.md`** — BE-11 added to status line; BE-11 row added to active tasks table; Task logs count: 45 → 46
- **`.ai_memory/_INDEX.md`** — Task logs count: 45 → 46; BE-11 entry added to task logs table

## Validation

- **PSParser tokenize:** All 9 scripts parse without errors ✅
- **`-DryRun` support:** All 9 scripts support `-DryRun` parameter ✅
- **No `.env` writes:** Confirmed by grep across all scripts ✅
- **No persistent env:** All `$env:` sets are process-scoped; `Remove-Item Env:` in `finally` blocks ✅
- **No `0.0.0.0`:** All bindings use `127.0.0.1` ✅
- **No port 3001:** Port 3001 excluded from all scripts ✅
- **No secrets:** No credentials, tokens, or keys in source code ✅
- **`Invoke-RestMethod` only:** No external HTTP clients, all API calls via localhost ✅

## Safety

- All scripts are local-only (no production/staging)
- No real OpenCode server was started during implementation
- No smoke tests were executed (scripts are authored, not run)
- No database changes (no migrations applied)
- No environment modifications outside the current process scope
- No `.env` file was created or modified

## Open Questions

None.

## Follow-up Tasks

- **BE-11 real smoke validation:** Execute `smoke-stub-runtime.ps1` and `smoke-real-opencode-runtime.ps1` against a running OpenCode 1.14.33 server to validate the scripts end-to-end.
- **BE-11 CI integration:** Optionally wire smoke scripts into a CI pipeline (GitHub Actions) for automated regression testing.
