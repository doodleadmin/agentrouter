# DEV-08C / VPS-08C — Telegram Mini App Foundation Implementation

Date: 2026-05-10  
Agent: studio-orchestrator (with frontend-developer + backend-architect)  
Status: **completed (local implementation only, not deployed)**

## Scope
- Implement local Mini App foundation in `apps/web`.
- Add Telegram WebApp client utility.
- Add backend WebApp initData auth endpoint.
- Add bot `/start` WebApp launch button surface.
- Add low-risk topic kind semantics validation (schema-level only, no migration).

## Implemented

### Frontend foundation (`apps/web`)
- Created real Vite + React + TypeScript app.
- Added mobile-first iOS-like UI shell with rounded cards, soft shadows, bottom nav.
- Added routes/pages:
  - `/` Dashboard
  - `/agents`
  - `/agents/:id`
  - `/tasks`
  - `/more`
- Added required components:
  - `AppShell`, `BottomNav`, `Header`, `StatusCard`, `AgentCard`, `QuickActionCard`,
  - `ActivityItem`, `AgentListItem`, `AgentDetailCard`, `StatusPill`, `PageContainer`.
- Added API client + mock fallback data for local preview.

### Telegram WebApp utility
- Added `apps/web/src/lib/telegram.ts`:
  - detects `window.Telegram?.WebApp`
  - calls `ready()` and `expand()`
  - safely exposes `initData` / `initDataUnsafe` for later auth handoff
  - browser fallback for local dev

### Backend Mini App auth endpoint
- Added `POST /telegram/webapp/auth`:
  - validates Telegram `initData` signature server-side using env `TELEGRAM_BOT_TOKEN`
  - returns minimal verified user payload
  - rejects invalid/missing payloads
- Added tests for valid/invalid cases.
- Replay protection noted as follow-up hardening step (not fully implemented in this stage).

### Bot WebApp launch surface
- Updated bot `/start` handler:
  - in private chat, if `TELEGRAM_WEBAPP_URL` configured, sends button **"Открыть AI Office"** via `WebAppInfo`
  - graceful fallback to plain text when URL is absent
- Added bot config key support for `TELEGRAM_WEBAPP_URL`.
- Added/updated bot tests.

### Topic semantics (low-risk)
- Added schema allowlist for topic kinds (no DB migration):
  - `general`, `agent`, `approvals`, `system_logs`, `task`

## Validation
- Frontend build: `npm run build` in `apps/web` ✅
- API targeted tests: `pytest tests/test_telegram_webapp_auth.py tests/test_telegram_topics.py` ✅ (10 passed)
- Bot targeted tests: `pytest tests/test_start_handler.py tests/test_tg04_config.py` ✅ (9 passed)

## Safety confirmations
- Not deployed to VPS.
- Production services not touched/restarted.
- Production DB not modified.
- Migrations not run.
- Telegram messages not sent by this task execution.
- OpenCode not started.
- Real agent tasks not run.
- Secrets not printed.

## Files changed (high-level)
- Frontend app scaffolding and UI in `apps/web/**`.
- API:
  - `apps/api/app/routers/telegram_webapp.py` (new)
  - `apps/api/app/schemas/telegram_webapp.py` (new)
  - `apps/api/app/services/telegram_webapp_auth.py` (new)
  - wiring updates in `main.py`, routers, tests.
- Bot:
  - `apps/telegram-bot/app/handlers/start.py`
  - `apps/telegram-bot/app/config.py`
  - tests.

## Next step
- DEV-08D: Mini App integration hardening
  - WebApp auth replay protection/session binding,
  - first real API-backed data flows,
  - topic-role orchestration policy enforcement (`general/approvals/system_logs`).
