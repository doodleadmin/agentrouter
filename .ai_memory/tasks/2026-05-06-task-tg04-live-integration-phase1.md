# TG-04: Live Integration Phase 1 — Security Prerequisites

**Date:** 2026-05-06  
**Agents:** security-engineer (requirements + review), backend-architect (implementation)  
**Status:** COMPLETE  
**Contour:** local only; without deploy/migrations/.env/secrets/real Telegram/OpenCode.

## Summary

Security prerequisites for TG-04 live Telegram bot integration IMPLEMENTED. Three layers hardened: configuration (admin user IDs with fail-closed parsing), message handling (bot message guard against feedback loops), and logging (secret redaction filter). New live runbook added.

## Changes

### 1. Config — Admin User IDs + env_file tuple
**File:** `apps/telegram-bot/app/config.py`
- Added `TELEGRAM_ADMIN_USER_IDS: str = ""` (comma-separated string, e.g. `"123456,789012"`)
- Added `admin_user_ids() -> set[int]` method with fail-closed parsing:
  - Splits on comma, strips whitespace, converts to int
  - Invalid/non-numeric entries → logged warning, silently excluded
  - Empty string → empty set
  - Trailing commas handled safely
- `env_file` changed from single `.env` to tuple `(".env", ".env.local")` for layered config

### 2. Bot Guard — is_bot message filter
**File:** `apps/telegram-bot/app/handlers/messages.py`
- Added guard at top of message handler: `if message.from_user and message.from_user.is_bot: return`
- Prevents worker notification feedback loop: bot's own messages (e.g., plan results echoed into topic) must not trigger new task creation
- Covers both plain text messages and slash-command messages from bots

### 3. Logging — SecretRedactionFilter (NEW)
**File:** `apps/telegram-bot/app/logging.py` (NEW)
- `SecretRedactionFilter(logging.Filter)` — redacts secrets from log records before output
- Compiled regex patterns (case-insensitive matching on log message string):
  - `TELEGRAM_BOT_TOKEN` — full token value patterns
  - OpenAI API keys (`sk-...`)
  - Bearer tokens (`Bearer eyJ...` or `Bearer sk-...`)
  - `DATABASE_URL` passwords (`postgresql://user:***@host`)
  - Redis passwords (`redis://:***@host`)
- Redacted values replaced with `[REDACTED]`
- Pre-compiled patterns for performance
- False-positive safe: partial matches (substrings without context) not redacted

### 4. Documentation — Live Runbook (NEW)
**File:** `docs/telegram-live-runbook.md` (NEW)
- Environment checklist (required env vars, token acquisition)
- Startup sequence (API → worker → bot)
- Abort criteria (errors, suspicious behavior, unexpected task creation)
- Safety gates before first live connect:
  - Verify `RUNTIME_PROVIDER=stub`
  - Verify `RUNTIME_ALLOW_REAL_OPENCODE_HTTP=false`
  - Verify `SANDBOX_RUNNER_MODE=fake`
  - Verify admin user IDs configured

## Tests (14 new)

### `test_tg04_config.py` (5 tests)
1. `test_admin_user_ids_valid` — `"123,456"` → `{123, 456}`
2. `test_admin_user_ids_empty` — `""` → `set()`
3. `test_admin_user_ids_whitespace` — `"123 , 456"` → `{123, 456}`
4. `test_admin_user_ids_invalid` — `"123,abc"` → `{123}` (abc silently excluded)
5. `test_admin_user_ids_trailing_comma` — `"123,"` → `{123}`

### `test_tg04_logging.py` (7 tests)
1. `test_token_redacted` — Telegram bot token pattern redacted
2. `test_openai_key_redacted` — `sk-` prefixed key redacted
3. `test_bearer_token_redacted` — Bearer auth header redacted
4. `test_db_password_redacted` — `DATABASE_URL` password redacted
5. `test_redis_password_redacted` — Redis password redacted
6. `test_no_false_positive` — normal text unchanged
7. `test_partial_match_safety` — incomplete patterns not redacted

### `test_messages.py` (+2 tests)
1. `test_is_bot_ignored` — message from `from_user.is_bot=True` silently skipped
2. `test_slash_from_bot_also_ignored` — `/start` command from bot also skipped (FakeBotMessage fixture)

## Changed Files (7 files)

| File | Status | Description |
|------|--------|-------------|
| `apps/telegram-bot/app/config.py` | Modified | +TELEGRAM_ADMIN_USER_IDS, +admin_user_ids(), env_file tuple |
| `apps/telegram-bot/app/handlers/messages.py` | Modified | +is_bot guard |
| `apps/telegram-bot/app/logging.py` | **NEW** | SecretRedactionFilter |
| `apps/telegram-bot/tests/test_tg04_config.py` | **NEW** | 5 admin ID parsing tests |
| `apps/telegram-bot/tests/test_tg04_logging.py` | **NEW** | 7 SecretRedactionFilter tests |
| `apps/telegram-bot/tests/test_messages.py` | Modified | +2 is_bot tests (FakeBotMessage) |
| `docs/telegram-live-runbook.md` | **NEW** | Live integration runbook |

## Guardrails preserved
- No live bot started (tests use mocked Telegram API)
- No `.env` or secrets changed
- No migrations run
- No deploy performed
- No OpenCode server started
- `RUNTIME_PROVIDER=stub`, `RUNTIME_ALLOW_REAL_OPENCODE_HTTP=false` defaults unchanged
- `SANDBOX_RUNNER_MODE=fake` default unchanged

## Verification
- `python -m compileall apps/telegram-bot/` — all files ✅
- `ruff check apps/telegram-bot/` — 0 errors ✅
- `pytest apps/telegram-bot/tests/ -v` — 64/64 ✅

## Next Steps
- TG-04 Phase 2: actual live bot connect with real Telegram token (requires user approval)
- Live checklist in `docs/telegram-live-runbook.md`
