# 2026-05-10 — DEV-08C: Backend/Bot safe stubs

## Summary
- Added API endpoint `POST /telegram/webapp/auth` to validate Telegram Mini App `initData` server-side using `TELEGRAM_BOT_TOKEN`.
- Added Telegram bot private `/start` WebApp launch button (`Открыть AI Office`) gated by `TELEGRAM_WEBAPP_URL` with graceful fallback when URL is not configured.
- Hardened `TelegramTopic` schema kinds to strict allowlist: `general | agent | approvals | system_logs | task` (no DB migration).

## Files touched
- `apps/api/app/routers/telegram_webapp.py`
- `apps/api/app/schemas/telegram_webapp.py`
- `apps/api/app/services/telegram_webapp_auth.py`
- `apps/api/app/main.py`
- `apps/api/app/routers/__init__.py`
- `apps/api/app/schemas/telegram_topic.py`
- `apps/api/tests/test_telegram_webapp_auth.py`
- `apps/api/tests/test_telegram_topics.py`
- `apps/telegram-bot/app/config.py`
- `apps/telegram-bot/app/handlers/start.py`
- `apps/telegram-bot/tests/test_start_handler.py`
- `apps/telegram-bot/tests/test_tg04_config.py`

## Validation
- `apps/api`: `pytest tests/test_telegram_webapp_auth.py tests/test_telegram_topics.py` → **10 passed**
- `apps/telegram-bot`: `pytest tests/test_start_handler.py tests/test_tg04_config.py` → **9 passed**

## Notes
- Replay protection is not fully implemented yet; TODO left in service docstring with recommendation: add auth_date age checks + one-time nonce/hash storage (Redis TTL).
