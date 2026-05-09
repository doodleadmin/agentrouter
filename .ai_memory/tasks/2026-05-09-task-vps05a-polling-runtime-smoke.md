# VPS-05A: Polling Runtime Smoke

**Date:** 2026-05-09
**Agent:** studio-orchestrator
**Status:** ✅ COMPLETED (read-only verification)
**Risk level:** low

---

## Objective

Verify the current polling-mode runtime is healthy on VPS 45.130.213.12 after ~24 hours since VPS-04 app start. No changes to VPS.

## Server

- **IP:** 45.130.213.12
- **SSH:** agentmc + root fallback
- **Repo:** `/opt/agent-control/agentrouter`, branch main, HEAD `f456c2a`
- **VS expected:** `f456c2a` (correct — `e94754b` is memory-only commits)

## Verifications

### STEP 4: API local health
- `curl -fsS http://127.0.0.1:8000/health`
- Result: `{"status":"ok","checks":{"api":"ok","database":"ok","redis":"ok"}}` ✅

### STEP 5: DB/Redis readiness
- Postgres (`pg_isready`): accepting connections ✅
- Redis (`redis-cli ping`): PONG ✅

### STEP 6: Worker health
- Container: docker-worker-1, healthy
- Celery v5.6.3, broker: Redis ✅
- 8 tasks registered: celery.backend_cleanup, plan_worker_task, execute_worker_task, complete_worker_task, live_reindex_worker_task, cleanup_worktree_worker_task, runtime_plan_worker_task, dequeue_worker_task
- Log sanitized — no errors

### STEP 7: Telegram bot health
- Container: docker-telegram-bot-1, healthy
- Bot: `@agentrouters_bot` (id=8749078276)
- Mode: long polling
- Log sanitized — no errors, polling active

### STEP 8: Telegram manual smoke
- **PASS** — user confirmed `@agentrouters_bot` responded

### STEP 9: No HTTPS / public exposure
- Caddy: NOT installed ✅
- UFW: active, only 22/tcp (OpenSSH) allowed inbound ✅
- Ports listening: `127.0.0.1:8000` (API internal), `0.0.0.0:22` (SSH), DNS resolver (53 localhost) ✅
- No 80/443 listeners ✅

## Container Status

| Container | State | Port |
|-----------|-------|------|
| docker-api-1 | Up healthy | 127.0.0.1:8000 |
| docker-postgres-1 | Up healthy | 5432 (internal) |
| docker-redis-1 | Up healthy | 6379 (internal) |
| docker-telegram-bot-1 | Up healthy | n/a (polling) |
| docker-worker-1 | Up healthy | n/a |

## What was NOT done

- ❌ No Caddy install
- ❌ No 80/443 opened
- ❌ No DNS changes
- ❌ No migrations
- ❌ No OpenCode tasks
- ❌ No app code changes
- ❌ No .env access (no values printed)
- ❌ No git push

## Next step

**VPS-05B**: DNS fix (polyrouter.ru → 45.130.213.12) + Caddy + HTTPS validation (when DNS is ready).

## Memory checkpoint

- **Memory updated:** yes
- **Files updated:** PROJECT_MEMORY.md, .ai_memory/current_state.md, .ai_memory/_INDEX.md
- **Commit:** not created
- **Skipped reason:** n/a
