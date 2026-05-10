# VPS-08H1B: Apply Bot WebApp Env Fix (production minimal)

**Date:** 2026-05-10
**Status:** completed
**Agent:** studio-orchestrator
**Risk:** medium (production container recreate only)

## Goal
Apply already pushed compose env pass-through fix (`66846fc`) so `telegram-bot` container receives `TELEGRAM_WEBAPP_URL` and `/start` can render Mini App button.

## Actions performed

1. **Preflight local check**
   - local branch clean/synced
   - latest commit: `66846fc fix(deploy): pass mini app env to telegram bot`

2. **Production baseline (read-only)**
   - SSH OK
   - server repo clean
   - containers healthy
   - `/health` OK
   - `/app/` HTTP 200
   - Caddy active

3. **Host env status (no values)**
   - `TELEGRAM_WEBAPP_URL=set`
   - `TELEGRAM_WEBAPP_AUTH_MAX_AGE_SECONDS=set`
   - `TELEGRAM_BOT_TOKEN=set`
   - `CALLBACK_SECRET=set`
   - `API_BASE_URL=set`

4. **Server fast-forward only**
   - `git fetch origin main && git pull --ff-only origin main`
   - server updated to `66846fc`
   - clean tree after pull

5. **Compose validation**
   - `docker compose ... config --quiet` => `COMPOSE_CONFIG_OK`
   - verified compose now contains:
     - `telegram-bot` env pass-through for `TELEGRAM_WEBAPP_URL`
     - `telegram-bot` + `api` pass-through for `TELEGRAM_WEBAPP_AUTH_MAX_AGE_SECONDS`

6. **Recreate telegram-bot only**
   - `docker compose ... up -d --no-deps telegram-bot`
   - no other services intentionally restarted

7. **Container env/settings verification (no values)**
   - inside `telegram-bot` container:
     - `TELEGRAM_WEBAPP_URL=set`
     - `TELEGRAM_WEBAPP_AUTH_MAX_AGE_SECONDS=set`
   - settings object:
     - `settings.TELEGRAM_WEBAPP_URL=set`
     - `settings.TELEGRAM_WEBAPP_AUTH_MAX_AGE_SECONDS=missing`
   - `can_build_webapp_button=yes` (critical success condition)

8. **User-assisted Telegram retest**
   - User confirmed: "Все работает и открывается"
   - `/start` now shows button
   - Mini App opens and navigation works

9. **Log checks (redacted)**
   - telegram-bot: polling healthy, updates handled, no traceback
   - api: health requests OK, no webapp 500 errors

10. **Final runtime health**
    - `/health` OK
    - `/app/` OK (HTTP 200)
    - all containers healthy
    - Caddy active
    - timers active
    - UFW unchanged

## Safety confirmations
- no `.env` changes
- no Caddy changes
- no migrations
- Docker daemon not restarted
- api/worker/postgres/redis not intentionally restarted
- no Telegram API manual sends
- no Telegram topics created
- no OpenCode
- no real tasks
- no secrets printed

## Notes
- `settings.TELEGRAM_WEBAPP_AUTH_MAX_AGE_SECONDS` remained "missing" in telegram-bot settings, but this does not block button rendering.
- Button rendering depends on `settings.TELEGRAM_WEBAPP_URL`, now confirmed set.

## Next step
- Optional hardening: align telegram-bot config schema to include `TELEGRAM_WEBAPP_AUTH_MAX_AGE_SECONDS` if required for future bot-side logic.
- Continue with broader Mini App UX smoke and auth-path verification if needed.
