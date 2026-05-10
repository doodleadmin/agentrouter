# Mini App Deployment Guide

## Overview

The Telegram Mini App is a static React app built with Vite, served under `/app/` on the same domain as the API. This approach keeps existing API endpoints and health monitoring unchanged.

## Architecture

```
https://polyrouter.ru/health        → API (unchanged)
https://polyrouter.ru/api/*         → API (unchanged)
https://polyrouter.ru/app/*         → Mini App static files (NEW)
https://polyrouter.ru/app           → Mini App index.html (NEW)
```

## Build

### Local development

```bash
cd apps/web
npm install
npm run dev        # http://localhost:5173
```

### Production build

```bash
cd apps/web
npm ci
npm run build:prod
```

Output: `apps/web/dist/` with all assets prefixed with `/app/`.

The `build:prod` script sets `VITE_BASE_PATH=/app/` so all asset URLs resolve correctly under the `/app/` path.

**Do NOT commit `dist/` to git.** It is gitignored.

## Deployment Steps (future — not yet executed)

### 1. Build locally or on server

```bash
cd apps/web
npm ci
npm run build:prod
```

### 2. Copy static assets to server

```bash
# Atomic deployment via symlink
REMOTE_PATH=/var/www/agentrouter-web
RELEASE_DIR=$REMOTE_PATH/releases/$(date +%Y%m%d%H%M%S)

ssh agentmc@45.130.213.12 "mkdir -p $RELEASE_DIR"
rsync -avz --delete apps/web/dist/ agentmc@45.130.213.12:$RELEASE_DIR/

# Atomic switch
ssh agentmc@45.130.213.12 "ln -sfn $RELEASE_DIR $REMOTE_PATH/current"
```

### 3. Update Caddyfile

Add the `/app/` handle block to Caddy (template provided in `infra/deploy/Caddyfile.miniapp`):

```
handle_path /app/* {
    root * /var/www/agentrouter-web/current
    try_files {path} /index.html
    file_server
}
```

Then reload Caddy:

```bash
sudo systemctl reload caddy
```

### 4. Configure bot WebApp URL

Add to `.env` on the server:

```
TELEGRAM_WEBAPP_URL=https://polyrouter.ru/app/
```

Restart only the telegram-bot service:

```bash
sudo systemctl restart agentrouter-telegram-bot
```

### 5. Validate

```bash
curl -s https://polyrouter.ru/health | jq .
# Expected: {"status":"ok",...}

curl -sI https://polyrouter.ru/app/
# Expected: 200, Content-Type: text/html

curl -sI https://polyrouter.ru/app/assets/
# Expected: 200 for JS/CSS assets
```

## Environment Variables

### Backend (.env)

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_WEBAPP_URL` | No | `https://polyrouter.ru/app/` | Enables Mini App launch button in bot `/start`. Empty = no button. |
| `TELEGRAM_BOT_TOKEN` | Yes | `123456:ABC-DEF...` | Telegram bot token (existing) |
| `CORS_ORIGINS` | No | `["https://polyrouter.ru"]` | Add production origin for CORS if needed |

### Frontend (build time, via VITE_ env vars)

| Variable | Build | Default | Description |
|----------|-------|---------|-------------|
| `VITE_BASE_PATH` | `build:prod` | `/app/` | Base path for all asset URLs |
| `VITE_API_BASE_URL` | Optional | `/api` | API base URL override. Default works when served from same origin. |

**No secrets are needed at build time.** The frontend only calls backend APIs at runtime.

## Rollback

1. Remove the `/app/` block from Caddyfile, reload Caddy
2. Restore previous `/var/www/agentrouter-web/current` symlink
3. Remove or empty `TELEGRAM_WEBAPP_URL` from `.env`
4. Restart telegram-bot service
5. Existing `/health` and API endpoints are never affected

## Caddy Template

A Caddyfile template for the Mini App is provided at `infra/deploy/Caddyfile.miniapp`.

This template is **documentation only** — it is NOT applied to production automatically.

## Security Notes

- Static files are public (no authentication required to load the app)
- All sensitive operations go through backend API with Telegram initData auth
- No secrets in frontend code or build artifacts
- CORS is handled by the backend, not Caddy
