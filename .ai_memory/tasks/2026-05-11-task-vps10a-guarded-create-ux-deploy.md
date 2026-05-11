# VPS-10A: Controlled Guarded Create + Approval UX Deploy

**Дата:** 2026-05-11
**Агент:** studio-orchestrator
**Контур:** production static frontend deploy only, no backend/infrastructure changes
**Предыдущий этап:** DEV-10A (local Safe Create + Approval UX)

---

## Цель

Задеплоить DEV-10A guarded create + approval UX на production VPS 45.130.213.12 через controlled static frontend deploy (zip artifact + atomic symlink switch).

---

## Precondition

- DEV-10A commit `aa2d803` pushed to origin/main ✅
- VPS runtime healthy: all 5 containers healthy, Caddy active, 4 timers active, UFW 22/80/443 ✅
- Server repo at `c81cb07` (VPS-09A deploy), clean tree ✅

---

## Выполнение

### Step 1: Server repo fast-forward

- `git fetch --all && git pull --ff-only` → `c81cb07..aa2d803` fast-forward ✅
- Clean tree confirmed ✅

### Step 2: Local build

- `npm run build:prod` PASS (63 modules, 0 errors) ✅
- Artifact: `miniapp-guarded-create-20260511-024932.zip`, SHA256 `6350dd0212ef1250f475828b8c9f7ee93e56aa13d23053a778e33e89ef135bc9`, 64973 bytes ✅

### Step 3: Upload + extract

- SCP to `/tmp/miniapp-guarded-create-20260511-024932.zip` ✅
- Extract to `/var/www/agentrouter-web/releases/20260510-225034/` ✅
- Permissions: `root:www-data`, dirs 755, files 644 ✅
- Note: accidental intermediate release `20260510-224945` created (duplicate from wrong deploy script pattern) — harmless, just extra directory

### Step 4: Atomic symlink switch

- `ln -sfn /var/www/agentrouter-web/releases/20260510-225034 /var/www/agentrouter-web/current` ✅
- Previous release preserved: `20260510-212126` (VPS-09A) ✅

### Step 5: Validation

- `/health` OK (api/db/redis all ok) ✅
- `/app/` HTTP 200, `<div id="root">` + assets present ✅
- All 5 containers healthy, Caddy active, 4 timers active, UFW unchanged ✅

### Step 6: User smoke test

- Navigation: Home / Agents / Tasks / Topics / Settings — all PASS ✅
- Create Agent flow: form → confirmation card shown (no submit) — PASS ✅
- Create Task flow: form → confirmation card shown (no submit) — PASS ✅
- Approvals card visible on HomePage — PASS ✅
- Guarded-mode indicator visible — PASS ✅

---

## Результаты

- **Production URL:** `https://polyrouter.ru/app/`
- **Active release:** `/var/www/agentrouter-web/releases/20260510-225034`
- **Rollback target:** `/var/www/agentrouter-web/releases/20260510-212126` (VPS-09A)
- **Rollback command:** `ln -sfn /var/www/agentrouter-web/releases/20260510-212126 /var/www/agentrouter-web/current` (static only, no infra changes)

---

## Safety

- No `.env` changes ✅
- No Caddy changes ✅
- No service restarts ✅
- No migrations ✅
- No Telegram API sends ✅
- No topics/data created ✅
- No OpenCode started ✅
- No real tasks executed ✅
- Secrets not printed ✅

---

## Memory checkpoint

- **Memory updated:** yes
- **Files updated:** PROJECT_MEMORY.md, current_state.md, _INDEX.md, this task log
- **Commit hash:** pending
