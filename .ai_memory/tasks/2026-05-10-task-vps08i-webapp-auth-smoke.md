# VPS-08I: Focused WebApp Auth Smoke + Safe Mini App API Validation

**Date:** 2026-05-10
**Status:** completed
**Agent:** studio-orchestrator
**Risk:** low-impact production smoke (read-only checks + user-assisted UX)

## Goal
Validate production Mini App auth path and read-only API UI after VPS-08H1B fix.

## Preflight

### Local
- `git status --short` clean
- `git status -sb` => `## main...origin/main`
- latest commit: `cc4ee5f docs(vps): record mini app telegram ux fix`

### Production baseline
- SSH OK
- server repo clean at `66846fc`
- all containers healthy
- `/health` OK
- `/app/` HTTP 200
- Caddy active

## Safe env/container status (values hidden)

### Host `.env` status
- TELEGRAM_WEBAPP_URL=set
- TELEGRAM_WEBAPP_AUTH_MAX_AGE_SECONDS=set
- TELEGRAM_BOT_TOKEN=set
- CALLBACK_SECRET=set
- DATABASE_URL=set
- REDIS_URL=set

### telegram-bot settings/container
- settings.TELEGRAM_WEBAPP_URL=set
- can_build_webapp_button=yes

## Log baseline marker
- `LOG_BASELINE_UTC=2026-05-10T20:33:12Z`

## User-assisted Telegram Mini App smoke

User result: **PASS**

- `/start` button appears: PASS
- Mini App opens: PASS
- Home: PASS
- Agents: PASS
- Tasks: PASS
- More: PASS
- Topic Bindings: PASS
- User report: "Да все работает"

No data creation performed:
- no agent create
- no task create
- no topic binding create
- no Telegram topics create

## WebApp auth/API log check

- API logs showed no `500` / traceback related to webapp auth path
- No sensitive payloads printed
- Known recurring `/health` 200 entries dominate tail (expected)

## Safe read-only API endpoint checks

(GET only; no bodies printed)

- `AGENTS_HTTP_STATUS=200`
- `TASKS_HTTP_STATUS=200`
- `EVENTS_HTTP_STATUS=200`
- `TOPICS_HTTP_STATUS=200`

No POST/creation requests executed.

## Bot logs summary

- polling healthy
- updates handled
- no traceback/errors

## Final runtime health

- `/health` OK
- `/app/` OK (HTTP 200)
- all containers healthy
- Caddy active
- timers active (4)
- UFW unchanged (22/80/443)

## Safety confirmations

- no deploy
- no code changes
- no `.env` changes
- no Caddy changes
- no service restarts
- no migrations
- no Telegram API manual sends
- no agents/tasks/topic bindings created
- no Telegram topics created
- no OpenCode
- no real tasks
- no secrets printed
- no raw `initData` printed
- no `session_token` printed

## Recommended next step
- Optional: add lightweight structured logging around successful `/telegram/webapp/auth` calls (without sensitive payloads) to improve observability in future smokes.
- Continue routine monitoring and proceed with feature-level Mini App QA checklist when needed.
