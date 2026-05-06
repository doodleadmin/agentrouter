# Task: DEV-LINUX-01B — Fix dry-run precondition behavior

**Date:** 2026-05-06
**Status:** completed
**Commit:** pending (unstaged)

## Context

DEV-LINUX-01 Phase 2 validation revealed that 5 out of 10 scripts had preconditions (curl, redis-cli, docker exec, API/OpenCode health checks) that executed BEFORE the `if $DRY_RUN` branch. This meant:
- 2 scripts (`start-api-opencode.sh`, `smoke-real-opencode-runtime.sh`) exited 1 in dry-run because OpenCode wasn't running
- 3 scripts (`start-worker.sh`, `start-telegram-bot.sh`, `smoke-stub-runtime.sh`) made real network connections in dry-run mode

## Fix

Wrapped all precondition blocks in `if ! $DRY_RUN` guards for 5 scripts:

| Script | Preconditions wrapped |
|--------|----------------------|
| `start-api-opencode.sh` | OpenCode health check, uvicorn check |
| `smoke-real-opencode-runtime.sh` | OpenCode health, API health, git baseline |
| `start-worker.sh` | Redis ping, API health, Celery check |
| `start-telegram-bot.sh` | .env.local check, API health |
| `smoke-stub-runtime.sh` | API health, git dirty check |

## Validation

- bash -n: 10/10 PASS
- --help: 10/10 PASS
- --dry-run: 10/10 PASS (all exit 0)
- No real connections made in dry-run
- No processes spawned
- .runtime/ and logs/dev/ empty
- No .env/secrets touched
- Non-dry-run behavior preserved

## Changed files

- `scripts/dev-linux/start-api-opencode.sh`
- `scripts/dev-linux/smoke-real-opencode-runtime.sh`
- `scripts/dev-linux/start-worker.sh`
- `scripts/dev-linux/start-telegram-bot.sh`
- `scripts/dev-linux/smoke-stub-runtime.sh`
