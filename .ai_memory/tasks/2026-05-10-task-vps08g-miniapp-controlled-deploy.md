# VPS-08G: Controlled Mini App Deploy

**Date:** 2026-05-10
**Status:** completed
**Agent:** studio-orchestrator
**Risk:** high (production changes, controlled)

## Goal
Deploy Telegram Mini App static frontend to production under:

- `https://polyrouter.ru/app/`

while preserving:

- `https://polyrouter.ru/health` unchanged
- API behavior unchanged
- runtime healthy
- rollback path

## Confirmation gate
`CONFIRM_VPS08G_MINIAPP_DEPLOY=yes` received before production actions.

## Preflight

### Local
- `git status --short` clean
- `git status -sb` => `## main...origin/main`
- latest local commit: `96a227b chore(miniapp): prepare deploy readiness`

### Production baseline
- SSH OK (`agentmc`, `root`)
- runtime healthy (api/postgres/redis/worker/telegram-bot healthy)
- `/health` OK
- Caddy active (`2.6.2`)
- Timers active (4)
- UFW unchanged (22/80/443)

## Artifact build

Built locally:

```bash
cd apps/web
npm run build:prod
```

Artifact created:
- `miniapp-dist-20260510-214207.zip`
- `SHA256=d8b9da1b1bdad3bfcc131c17859de1824353ee272e033cd2fb90b94b8f265e68`

`apps/web/dist` remained local-only (not staged).

## Server repo sync

Server repo `/opt/agent-control/agentrouter`:
- clean before pull
- `git fetch origin main && git pull --ff-only origin main`
- fast-forward: `f456c2a -> 96a227b`
- no merge commit, no reset

## Static deploy

1. Uploaded artifact to `/tmp/miniapp-dist-20260510-214207.zip`
2. Extracted to release path:
   - `/var/www/agentrouter-web/releases/20260510-174338`
3. Switched symlink:
   - `/var/www/agentrouter-web/current -> /var/www/agentrouter-web/releases/20260510-174338`
4. Applied safe perms:
   - dirs `755`, files `644`, owner `root:www-data`

## Caddy live update (controlled)

- Backed up Caddyfile:
  - `/etc/caddy/Caddyfile.bak.20260510-174411`
- Deployed config with:
  - `redir /app /app/ 308`
  - `handle_path /app/*` static serving from `/var/www/agentrouter-web/current`
  - fallback `handle { reverse_proxy 127.0.0.1:8000 }` to preserve API routes
- `caddy validate` => valid
- `systemctl reload caddy` => active

## Production env update (safe keys only)

Backed up env:
- `.env.bak.vps08g.20260510-174504`

Updated keys (no secret output):
- `TELEGRAM_WEBAPP_URL` => set
- `TELEGRAM_WEBAPP_AUTH_MAX_AGE_SECONDS` => set (`300`)

Verified only set/missing status for sensitive keys, without values.

## Rebuild/recreate scope

Executed:
- `docker compose ... build api telegram-bot`
- `docker compose ... up -d --no-deps api telegram-bot`

Intentionally NOT restarted:
- postgres
- redis
- worker
- docker daemon

## Validation

- `https://polyrouter.ru/health` => OK (status `ok`)
- `https://polyrouter.ru/app/` => HTTP 200
- index markers present:
  - `<div id="root"></div>`
  - `/app/assets/index-...`
- `POST /telegram/webapp/auth` with `{}` => HTTP `422` (safe-fail, not 500)
- containers healthy (`api`, `telegram-bot`, `worker`, `postgres`, `redis`)
- Caddy active
- timers active (4)
- UFW unchanged

## Logs check (redacted)

- API logs show expected `422` for empty webapp auth payload test
- telegram-bot logs show normal polling startup
- no secret values surfaced

## Rollback assets and plan

### Assets
- Caddy backup: `/etc/caddy/Caddyfile.bak.20260510-174411`
- env backup: `/opt/agent-control/agentrouter/.env.bak.vps08g.20260510-174504`
- static releases: `/var/www/agentrouter-web/releases/*`

### Plan
1. Restore Caddy backup and reload Caddy
2. Restore `.env` backup and recreate `api` + `telegram-bot`
3. Repoint `/var/www/agentrouter-web/current` to previous release
4. Verify `/health`

## Safety confirmations
- no migrations run
- production DB data not touched
- docker daemon not restarted
- postgres/redis/worker not intentionally restarted
- Telegram messages not sent manually
- Telegram topics not created
- OpenCode not started
- real agent tasks not run
- secrets not printed
