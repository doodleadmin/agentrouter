# VPS-08H1A: Compose WebApp Env Pass-through Patch (local)

**Date:** 2026-05-10
**Status:** completed (local patch only)
**Agent:** studio-orchestrator
**Risk:** low (local config/docs/memory changes only)

## Context

VPS-08H diagnostics confirmed root cause for missing Mini App button in `/start`:

- Host `.env`: `TELEGRAM_WEBAPP_URL` set
- `telegram-bot` container env: `TELEGRAM_WEBAPP_URL` missing
- `settings.TELEGRAM_WEBAPP_URL` inside bot: missing
- `/start` handler shows button only if `is_private and settings.TELEGRAM_WEBAPP_URL`

Therefore, compose env pass-through was incomplete.

## Patch applied

### File: `infra/docker/docker-compose.prod.yml`

#### Service `telegram-bot`
Added explicit env pass-through:

- `TELEGRAM_WEBAPP_URL: ${TELEGRAM_WEBAPP_URL:-}`
- `TELEGRAM_WEBAPP_AUTH_MAX_AGE_SECONDS: ${TELEGRAM_WEBAPP_AUTH_MAX_AGE_SECONDS:-300}`

#### Service `api`
Added for consistency with auth hardening config:

- `TELEGRAM_WEBAPP_AUTH_MAX_AGE_SECONDS: ${TELEGRAM_WEBAPP_AUTH_MAX_AGE_SECONDS:-300}`

No secrets added, no `.env` value changes.

## Validation

- `git diff -- infra/docker/docker-compose.prod.yml` reviewed ✅
- `git diff --check` no issues ✅
- Local compose syntax check:
  - `docker compose -f infra/docker/docker-compose.prod.yml --env-file .env.example config --quiet` ✅

## Docs

Updated `docs/miniapp-deploy.md` with a concise note:
- production compose must pass `TELEGRAM_WEBAPP_URL` into `telegram-bot`
- otherwise `/start` button is missing even when host `.env` is set

## Safety

- No deploy
- No VPS changes
- No `.env` changes
- No service restarts
- No migrations
- No Telegram messages
- No topics created
- No OpenCode
- No real tasks
- No secrets printed

## Next step

1. Commit + push this patch
2. VPS-08H1B: fast-forward server repo, recreate **telegram-bot only** (and api only if desired for consistency), then retest `/start` button.
