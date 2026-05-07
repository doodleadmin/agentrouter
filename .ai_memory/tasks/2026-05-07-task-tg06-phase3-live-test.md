# TG-06 Phase 3: Live Compact Callback E2E

- **Date:** 2026-05-07
- **Agent:** studio-orchestrator
- **Contour:** live WSL2 Ubuntu 22.04; live Telegram bot + Celery worker + API stub + native PostgreSQL 14 + Redis.
- **Goal:** Validate compact Telegram callback protocol end-to-end with live inline button interaction.

## Summary

TG-06 Phase 3 live test validated the compact Telegram callback protocol end-to-end: a medium-risk task was created via worker, plan was generated, user clicked the Approve inline button, and the entire approve flow completed successfully with callback validation at every step.

## What was tested

1. **Medium-risk task creation:** task-0002 via Celery worker → status waiting_approval
2. **Plan generation:** plan_text produced, approval record fb8f305a created (pending)
3. **User interaction:** User typed /status, received inline keyboard with Approve button
4. **Callback data:** 38 bytes `v1:a:task-0002:<exp_base36>:<sig16>` (under Telegram's 64-byte limit)
5. **Callback validation:** POST /callback-answer → 200 OK, `action_valid=true`, correct action=approve
6. **Approve flow:** POST /approvals/fb8f305a/approve → 200 OK
7. **Status transitions:** task waiting_approval → approved; approval pending → approved, approved_by=1113930428

## Bugs found & fixed during live test

### Bug 1: CALLBACK_SECRET mismatch
- **Root cause:** `start-api-stub.sh` doesn't load `.env.local`, so API used empty CALLBACK_SECRET default. Bot used correct secret from `.env.local` → all callback HMAC signatures were rejected by API-side validation.
- **Fix:** Created `~/agentrouter/.env` with CALLBACK_SECRET. Script `start-api-stub.sh` sources `.env` (not `.env.local`), so the API now picks up CALLBACK_SECRET correctly.

### Bug 2: project.repo_path invalid
- **Root cause:** DB had `repo_path=/opt/agent-control/repos/agentrouter` which doesn't exist on the server.
- **Fix:** Updated project record to `repo_path=/root/agentrouter`.

## Services tested

| Service | Details |
|---------|---------|
| API stub | uvicorn :8000, provider=stub |
| Celery worker | WSL process, SIGHUP fix active |
| Telegram bot | @agentrouters_bot, long polling |
| PostgreSQL | Native Linux package, PostgreSQL 14 |
| Redis | Native Linux package |

## Validation baseline

| Component | Tests | Result |
|-----------|-------|--------|
| API | 275/275 | ✅ PASS |
| Telegram-bot | 79/79 | ✅ PASS |
| Worker | 98/98 | ✅ PASS |
| ruff | — | clean |

## Key findings

- **No BUTTON_DATA_INVALID errors** in any logs — compact callback protocol works correctly with Telegram's inline keyboard API.
- 38-byte callback data leaves significant headroom under Telegram's 64-byte limit (40% margin).
- Compact callback protocol with HMAC signatures is production-viable for inline Telegram buttons.

## Result

**COMPLETE** — Compact Telegram callback protocol validated end-to-end. All status transitions, approval flows, and callback validations passed.
