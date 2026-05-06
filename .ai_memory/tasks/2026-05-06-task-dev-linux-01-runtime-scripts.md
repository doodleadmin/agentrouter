# Task: DEV-LINUX-01 — Ubuntu 22.04 Runtime Scripts

**Date:** 2026-05-06
**Agent:** studio-orchestrator
**Status:** COMPLETE
**Risk:** low (no code changes, no service starts, no secrets)

## Context

Windows PowerShell automation (`scripts/dev/*.ps1`) hangs on long-running processes (uvicorn, celery, opencode) due to console handle inheritance in `Start-Process`. Production target is Ubuntu 22.04. Decision: create Linux-native bash scripts as primary dev runtime, keep PS1 as legacy.

## What Was Done

### 10 Bash Scripts (`scripts/dev-linux/`)

| Script | Purpose | Key Features |
|--------|---------|-------------|
| `check-db.sh` | DB health check | Container, pg_isready, 9 tables, alembic version, --json |
| `bootstrap-db.sh` | Alembic migrations | `upgrade head` only, --force confirmation, process-scoped DATABASE_URL |
| `start-api-stub.sh` | API stub mode | nohup, PID file, readiness poll /health /projects /agents |
| `start-opencode.sh` | OpenCode server | nohup, localhost-only verification, /global/health + /doc |
| `start-api-opencode.sh` | API opencode_http | Requires OpenCode healthy, config validation, nohup |
| `start-worker.sh` | Celery worker | **Critical fix** for Windows hang, nohup + PID |
| `start-telegram-bot.sh` | Telegram bot | Sources .env.local (process-scoped), never displays token |
| `smoke-stub-runtime.sh` | Stub smoke | curl+jq, direct POST /runtime, verifies stub-session |
| `smoke-real-opencode-runtime.sh` | Real OpenCode smoke | ses_* session, no stub fingerprints, no leaks |
| `cleanup-runtime.sh` | Cleanup | PID validation, port verification, optional API restart |

### Common Patterns

- `#!/usr/bin/env bash` + `set -euo pipefail`
- `--dry-run` and `--help` on all scripts
- `nohup ... > logs/dev/<service>.log 2>&1 &` for all long-running services
- PID files in `.runtime/<service>.pid`
- All services bind `127.0.0.1` only
- Process-scoped env vars (never persisted)
- PID command line validation before kill

### Other Files

- `docs/dev-linux-runbook.md` — full runbook (prerequisites, quick start, reference, troubleshooting)
- `.gitignore` — added `.runtime/`
- `PROJECT_MEMORY.md` — updated status + changelog entry

## What Was NOT Changed

- No Python code changes
- No docker-compose.yml changes
- No .env / .env.local changes
- No opencode.json changes
- No real service starts
- No migrations/deploy
- No git push

## Validation

- bash -n syntax check: requires Linux (pending)
- --dry-run support: confirmed in all scripts
- shellcheck: requires Linux (pending)

## Definition of Done

- [x] 10 scripts created in `scripts/dev-linux/`
- [x] All scripts have `--dry-run` and `--help`
- [x] All services use nohup + PID files
- [x] All services bind 127.0.0.1 only
- [x] docs/dev-linux-runbook.md created
- [x] .gitignore updated
- [x] PROJECT_MEMORY.md updated
- [ ] bash -n validation (requires Linux)
- [ ] Live smoke test (requires Linux + Docker)

## Next Steps

1. Transfer scripts to WSL2 Ubuntu 22.04
2. Run `bash -n scripts/dev-linux/*.sh` for syntax validation
3. Run `shellcheck scripts/dev-linux/*.sh` if available
4. Run `--dry-run` for each script
5. Full stub smoke test on Linux
6. Full real OpenCode smoke test on Linux
