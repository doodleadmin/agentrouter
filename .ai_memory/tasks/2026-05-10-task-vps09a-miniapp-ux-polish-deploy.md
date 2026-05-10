# VPS-09A: Controlled Mini App UX Polish Deploy

**Date:** 2026-05-10
**Status:** completed
**Agent:** studio-orchestrator
**Risk:** medium (production static file update, no backend changes)

## Goal
Deploy DEV-09A frontend UX polish to production Mini App `https://polyrouter.ru/app/` without changing backend, .env, Caddy, or service state.

## Preflight

### Local
- `git status --short` clean
- `git status -sb` => `## main...origin/main`
- latest commit: `c81cb07 feat(miniapp): polish production ux dashboards`

### Production baseline (before deploy)
- SSH OK
- server repo clean at `66846fc`
- all 5 containers healthy
- `/health` OK
- `/app/` 200
- Caddy active
- Current release: `/var/www/agentrouter-web/releases/20260510-174338`
- UFW unchanged (22/80/443)

## Server fast-forward
- `66846fc..c81cb07` fast-forward clean
- 17 files, +814/-92 lines
- latest commit: `c81cb07 feat(miniapp): polish production ux dashboards`
- working tree clean

## Build artifact
- Local build: `npm run build:prod` PASS (tsc + vite, 0 errors, 61 modules)
- File: `miniapp-ux-polish-20260511-012032.zip`
- SHA256: `b6eac4e37578146ae484e55c73af4377fd23e97d8c8ebca511c415c9bf815ea0`
- Size: 63639 bytes

## Deploy
- Uploaded to VPS `/tmp/`
- New release: `/var/www/agentrouter-web/releases/20260510-212126`
- Previous release: `/var/www/agentrouter-web/releases/20260510-174338`
- Symlink atomically switched: `current` → `20260510-212126`
- Permissions: `root:www-data`, dirs 755, files 644
- `STATIC_INDEX_OK`

## Validation

### /health
```json
{"status":"ok","checks":{"api":"ok","database":"ok","redis":"ok"}}
```
✅

### /app/
- HTTP 200 ✅
- `<div id="root">` present ✅
- Assets: `/app/assets/index-CHDR1Kuc.js` ✅
- CSS: `/app/assets/index-BC7uwLyL.css` ✅

### User-assisted Mini App UX smoke
- /start button: PASS ✅
- Mini App opens: PASS ✅
- No white screen: PASS ✅
- Home page loads: PASS ✅
- Mode indicator visible: PASS ✅
- Agents page loads: PASS ✅
- Tasks page loads: PASS ✅
- Settings page (formerly More): PASS ✅
- Settings shows safe auth/session status only: PASS ✅
- No raw session_token visible: PASS ✅
- No raw initData visible: PASS ✅
- Topic Bindings: PASS ✅
- Role explanation cards visible: PASS ✅
- User report: "All good, looks great without secrets"

No agents/tasks/topic bindings created. No Telegram topics created.

### Read-only API checks
- `/agents` → 200 ✅
- `/tasks` → 200 ✅
- `/events` → 200 ✅
- `/telegram/topics` → 200 ✅

### Logs summary
- API logs: clean (no webapp/auth 500s, no traceback) ✅
- Bot logs: healthy (polling active, no errors/exceptions) ✅

### Final runtime health
- `/health` OK ✅
- `/app/` 200 ✅
- All 5 containers healthy ✅
- Caddy active ✅
- 4 timers active ✅
- UFW unchanged (22/80/443) ✅

## Rollback plan

Assets available:
- Previous release: `/var/www/agentrouter-web/releases/20260510-174338`
- Current release: `/var/www/agentrouter-web/releases/20260510-212126`

Rollback command (if needed):
```bash
ln -sfn /var/www/agentrouter-web/releases/20260510-174338 /var/www/agentrouter-web/current
```
No Caddy/.env/service changes needed — static file rollback only.

## Safety confirmations

- No .env changes ✅
- No Caddy changes ✅
- No service restarts ✅
- No migrations ✅
- No DB data changes ✅
- No Telegram API manual sends ✅
- No agents/tasks/topic bindings created ✅
- No Telegram topics created ✅
- OpenCode not started ✅
- Real tasks not run ✅
- Secrets not printed ✅
- Raw initData not printed ✅
- Raw session_token not printed ✅

## Recommended next step
- Continue routine monitoring
- Proceed with further Mini App features (topic orchestration, agent task flow, etc.)
