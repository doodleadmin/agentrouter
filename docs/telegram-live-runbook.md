# Telegram Live Integration Runbook — TG-04 Phase 1

> **Status:** Security prerequisites implemented. Live bot NOT yet connected.
> **Date:** 2026-05-06
> **Commit chain:** c056b22 (TG-03) → TG-04 Phase 1 security prep

## Architecture

```
┌─────────────────┐     HTTP (polling)      ┌─────────────────┐
│  Telegram Group  │ ←───────────────────────│  Bot (aiogram)   │
│  (test only!)    │ ───────────────────────→│  api_client.py   │
└─────────────────┘                          └────────┬────────┘
                                                      │ HTTP
                                             ┌────────▼────────┐
                                             │  API (FastAPI)   │
                                             │  127.0.0.1:8000  │
                                             └─────────────────┘
```

Bot is **API-only** — no DB access, no OpenCode direct, no runtime execution.

## Environment Variables

Use `.env.local` for your personal token/credentials (gitignored by `*.local`).

```bash
# REQUIRED (in .env.local, NEVER committed):
TELEGRAM_BOT_TOKEN=9999999999:XXXXXXXXXXXXXXXXXXXXXXXXXXXX
CALLBACK_SECRET=<random-64-hex-chars>

# STRONGLY RECOMMENDED:
TELEGRAM_ADMIN_USER_IDS=123456789                  # your Telegram user ID

# OPTIONAL (defaults work for local dev):
API_BASE_URL=http://127.0.0.1:8000
API_TIMEOUT_SECONDS=10.0

# SAFETY DEFAULTS (keep these for local test):
RUNTIME_PROVIDER=stub                              # no real OpenCode
DEBUG=false
```

Config reads `.env` first, then `.env.local` (overrides). Both are gitignored.

## Startup (Minimal — No Worker, No OpenCode)

```bash
# 1. Ensure DB + Redis are up
docker compose -f infra/docker/docker-compose.yml up -d postgres redis

# 2. Start API (stub mode) in one terminal
uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000 --reload

# 3. Start bot (polling) in another terminal
cd apps/telegram-bot
python -m app.main
```

## Abort Criteria

Stop bot immediately if:
1. `TELEGRAM_BOT_TOKEN` or `CALLBACK_SECRET` appears in any log line
2. Bot sends a message to a chat/channel it wasn't configured for
3. `approve` or `reject` succeeds from a non-admin user
4. API returns 500 on any endpoint repeatedly
5. Forged `callback_data` is accepted by API

## Safety Gates (TG-04 Phase 1)

| Gate | File | Description |
|------|------|-------------|
| **is_bot filter** | `handlers/messages.py` | Worker notifications (from_user.is_bot=True) are ignored — no feedback loop |
| **Admin allowlist** | `config.py` → `TELEGRAM_ADMIN_USER_IDS` | Comma-separated Telegram user IDs; empty = admin actions fail-closed |
| **Secret redaction** | `logging.py` → `SecretRedactionFilter` | Bot tokens, API keys, DB/Redis passwords masked in logs |
| **`.env.local`** | `config.py` → `env_file=(".env",".env.local")` | Personal overrides never committed |

## Live Test Checklist (Phase 2)

When ready to connect real Telegram:
1. Create a **test bot** via @BotFather (separate from production)
2. Create a **test group** or use **private chat with bot**
3. Set `TELEGRAM_BOT_TOKEN` in `.env.local` (test bot token)
4. Set `TELEGRAM_ADMIN_USER_IDS` to your user ID
5. Run pre-flight checks from `docs/tg04-live-test-checklist.md` (if created)
6. Start API + bot
7. Execute Phase A tests (private chat) from TG-04 QA checklist
8. Execute Phase B tests (forum topic) if Phase A passes
9. Stop bot, verify git clean, verify no leaked messages

## Related Docs

- `docs/telegram-flow.md` — Telegram routing and topic design
- `docs/security-policy.md` — Risk levels, permissions, sandbox rules
- `docs/architecture.md` — System boundaries and component responsibilities
- TG-04 QA checklist — 25-step live test procedure (from TG-04 planning)
