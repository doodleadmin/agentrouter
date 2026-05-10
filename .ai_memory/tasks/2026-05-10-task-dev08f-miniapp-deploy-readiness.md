# DEV-08F: Mini App Deploy Readiness

**Date:** 2026-05-10
**Status:** completed
**Agent:** studio-orchestrator
**Risk:** low (local docs/config only)

## Goal
Prepare Telegram Mini App for future controlled VPS deploy without touching production.

## Chosen deployment strategy
**Option B: `/app/` path on same domain**

Why safer:
- Keeps `https://polyrouter.ru/health` unchanged
- Keeps existing API routes/proxy unchanged
- No DNS changes required
- Low blast radius rollback
- Telegram bot can use `TELEGRAM_WEBAPP_URL=https://polyrouter.ru/app/`

## Changes made

### 1) Web build readiness
- `apps/web/vite.config.ts`
  - Added configurable `base` from `VITE_BASE_PATH` (default `/`)
- `apps/web/package.json`
  - Added `build:prod` script:
    - `vite build --base /app/`

### 2) Frontend API base readiness
- `apps/web/src/api/client.ts`
  - `API_BASE` now supports env override via `VITE_API_BASE_URL` (default `/api`)
  - Enables same-origin `/api` in production while retaining override flexibility

### 3) Env documentation
- `.env.example`
  - Added `TELEGRAM_WEBAPP_URL=` with comments and example `/app/` URL
  - No secrets added

### 4) Deploy docs / runbook
- Added `docs/miniapp-deploy.md`
  - Build commands (`npm ci`, `npm run build:prod`)
  - Output path: `apps/web/dist`
  - Target server path: `/var/www/agentrouter-web/current`
  - Future controlled copy/symlink strategy
  - Validation checklist (`/health`, `/app/`)
  - Rollback steps
  - Env variables (`TELEGRAM_WEBAPP_URL`, `VITE_API_BASE_URL`, `VITE_BASE_PATH`)

### 5) Caddy template (docs-only)
- Added `infra/deploy/Caddyfile.miniapp` (template snippet only)
  - `handle_path /app/*` static serving
  - SPA fallback with `try_files ... /index.html`
  - Cache headers for static assets
- Updated `infra/deploy/Caddyfile` comments to reference `/app/` future block

### 6) Local helper script template
- Added `scripts/build-miniapp.sh`
  - Local-only build helper
  - No SSH, no deploy, no production writes
  - Prints artifact path and next manual steps

### 7) Web README update
- Rewrote `apps/web/README.md` for deploy readiness:
  - `build:prod` usage
  - env vars
  - routes
  - deployment doc link

## Build/test results
- `npm run build` ✅ PASS
- `npm run build:prod` ✅ PASS
- `apps/web/dist` exists locally and is **not staged**

## Security/safety
- No deploy executed
- No SSH/VPS changes
- Production untouched
- Live Caddy unchanged
- Services not restarted
- Migrations not run
- Telegram messages not sent
- Telegram topics not created
- OpenCode not started
- Real agent tasks not run
- Secrets not printed

## Next recommended stage
**VPS-08G: Controlled Mini App deploy**
- Apply Caddy `/app/` block on VPS
- Upload `dist` to `/var/www/agentrouter-web/current`
- Set `TELEGRAM_WEBAPP_URL=https://polyrouter.ru/app/`
- Restart bot only
- Validate `/health` unaffected
