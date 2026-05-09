# VPS-04: Controlled Migration + App Start

**Date:** 2026-05-09
**Agent:** studio-orchestrator
**Status:** ✅ COMPLETED
**Risk level:** HIGH (DB migrations + first production app start on VPS)

---

## Objective

Run Alembic migrations and start all application services (API, Worker, Telegram bot) on VPS 45.130.213.12. Three explicit confirmation gates required.

## Server

- **IP:** 45.130.213.12
- **User:** agentmc (root fallback confirmed)
- **OS:** Ubuntu 24.04.4 LTS
- **Docker:** 29.4.3, Compose v5.1.3
- **Swap:** 2.0 GiB

## What was done

### Step 0: Local safety check
- Git status clean, HEAD `f456c2a`, branch `main`, synced with `origin/main` ✅

### Step 1: Confirmation Gate #1
- `CONFIRM_VPS04_START=yes` — confirmed ✅

### Step 2: Server baseline
- agentmc SSH OK ✅
- root fallback OK ✅
- swap 2G active ✅
- Docker 29.4.3 OK ✅
- UFW active, SSH-only (22/tcp) ✅

### Step 3: Fast-forward server repo
- From `7494931` to `f456c2a` (ff-only) ✅
- `.env` gitignored ✅
- Clean working tree after ff ✅

### Step 4: .env verification (without values)
- Owner/mode: `agentmc:agentmc 600` ✅
- All 12 required keys set ✅
- `RUNTIME_PROVIDER` missing but defaults to `"stub"` in code — safe ✅
- DEBUG safe (not `true`) ✅
- SQL_ECHO safe (not `true`) ✅
- Telegram token: placeholder cleared, format OK ✅
- Telegram admin IDs: placeholder cleared, format OK ✅
- **Note:** `POSTGRES_USER=CHANGE_ME` — placeholder became actual postgres username during container init in VPS-03B. Non-critical.

### Step 5: Compose config + current services
- Compose config rendered OK ✅
- Services: api, postgres, redis, telegram-bot, worker ✅
- Only postgres + redis running (10h uptime, healthy) ✅

### Step 6: DB backup before migrations
- Backup: `pre-vps04-20260509-174325.sql` (695 bytes, empty DB as expected) ✅
- Stored in `/var/lib/agentrouter/backups/` ✅

### Step 7: Confirmation Gate #2
- `CONFIRM_VPS04_MIGRATIONS=yes` — confirmed ✅

### Step 8: Run Alembic migrations
- Docker images built: api, worker, telegram-bot ✅
- Migration `0001_initial_all_tables` → applied ✅
- Migration `0002_add_security_audit_events` → applied ✅
- Alembic current: `0002_add_security_audit_events (head)` ✅
- Migrations used `POSTGRES_USER=CHANGE_ME` for DB connection (expected given .env state)

### Step 9: Confirmation Gate #3
- `CONFIRM_VPS04_APP_START=yes` — confirmed ✅

### Step 10: Start API
- Container `docker-api-1`: started, healthy ✅
- Bound to `127.0.0.1:8000` (not public) ✅
- `/health` response: `{"status":"ok","checks":{"api":"ok","database":"ok","redis":"ok"}}` ✅

### Step 11: Start Worker
- Container `docker-worker-1`: started, healthy ✅
- celery@8364499cb3d0 ready ✅
- 8 tasks registered (agent_execute, agent_plan, deploy_production, deploy_staging, healthcheck, memory_index, send_notification, telegram_inbound) ✅

### Step 12: Start Telegram Bot
- Container `docker-telegram-bot-1`: started, healthy ✅
- Bot: @agentrouters_bot (ID: 8749078276) ✅
- Polling mode active ✅

### Step 13: Final runtime verification
- All 5 containers healthy (api, postgres, redis, worker, telegram-bot) ✅
- `/health`: `status: ok` ✅
- DB accepting connections ✅
- Redis PONG ✅
- Port 8000: `127.0.0.1` only ✅
- Ports 80/443: closed ✅
- UFW: SSH-only ✅

### Step 14: Optional Telegram manual smoke
- **Pending user confirmation** — @agentrouters_bot is polling, send `/start` or `/help` to test
- Status: `NOT_TESTED` (will update when confirmed)

## What was NOT done

- ❌ Ports 80/443 NOT opened
- ❌ Caddy NOT installed
- ❌ OpenCode NOT started
- ❌ No real agent task executions
- ❌ No destructive DB operations
- ❌ No rollback executed
- ❌ No application code changes
- ❌ No infra/deploy script changes
- ❌ No git push from orchestrator
- ❌ No secrets printed

## Known warnings / observations

| Item | Severity | Note |
|------|----------|------|
| `POSTGRES_USER=CHANGE_ME` | ⚠️ Low | Placeholder became actual postgres username during VPS-03B container init. All connections use this username. Non-critical but should be addressed in future cleanup. |
| No domain/Caddy | ⚠️ Medium | API is only accessible via SSH tunnel or localhost. Not publicly reachable. |
| Telegram live smoke not confirmed | ⚠️ Low | Bot is polling but no message has been sent to verify response. |

## Production deploy claim

**VPS-04 IS the real production deploy.** Application is running with 5 healthy containers, database migrated, and Telegram bot polling.

## Current runtime state

| Service | Container | Status | Port |
|---------|-----------|--------|------|
| API | docker-api-1 | healthy | 127.0.0.1:8000 |
| Worker | docker-worker-1 | healthy | — |
| Telegram Bot | docker-telegram-bot-1 | healthy | — |
| PostgreSQL | docker-postgres-1 | healthy | 5432 (internal) |
| Redis | docker-redis-1 | healthy | 6379 (internal) |

## Memory checkpoint

- **Memory updated:** yes
- **Files updated:** PROJECT_MEMORY.md, .ai_memory/current_state.md, .ai_memory/_INDEX.md
- **Commit:** NOT created (pending separate approval)
- **Skipped reason:** n/a
