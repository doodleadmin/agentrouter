# DOP-03 Phase 2: Production Runtime Templates + Enhanced Health Check

**Дата:** 2026-05-08
**Агент:** studio-orchestrator
**Контур:** local only; без deploy/migrations/.env/secrets/OpenCode/live Telegram.
**Статус:** ✅ COMPLETE

## Цель

Create production runtime templates and enhance /health endpoint with DB/Redis dependency checks.

## Что сделано

### Enhanced /health endpoint

- **Файл:** `apps/api/app/routers/health.py`
- Добавлены `_check_database()` (SELECT 1 via AsyncSessionLocal) и `_check_redis()` (ping via redis.asyncio)
- Response теперь включает `checks` dict: `{api: "ok", database: "ok"|"error", redis: "ok"|"error"|"unavailable"}`
- `status: "ok"` когда все checks ok, `"degraded"` когда DB или Redis error
- HTTP 200 всегда (backward compatible)
- Существующие поля (service, version, timestamp) сохранены
- Никакие secrets/connection strings не раскрываются

### Caddyfile template

- **Файл:** `infra/deploy/Caddyfile`
- Placeholders: `{$AGENTROUTER_DOMAIN}`, `{$AGENTROUTER_TLS_EMAIL}`
- Reverse proxy to 127.0.0.1:8000 для API endpoints
- Comments для future webhook/dashboard
- JSON access logs с rotation (100mb, 10 files)
- gzip + zstd compression

### systemd unit templates

- **agentrouter-api.service** — `uvicorn app.main:app --host 127.0.0.1 --port 8000`
- **agentrouter-worker.service** — `celery -A app.celery_app worker --loglevel=info --pool=solo --queues=...`
- **agentrouter-telegram-bot.service** — `python -m app.main`
- Все: User=agentmc, NoNewPrivileges=true, PrivateTmp=true, ProtectSystem=strict, ReadWritePaths=logs, journald logging
- EnvironmentFile=/opt/agent-control/agentrouter/.env (no inline secrets)
- Entry points сверены с существующими dev scripts

### Production Docker Compose

- **Файл:** `infra/docker/docker-compose.prod.yml`
- Services: postgres (pgvector/pg16), redis (7-alpine), api, worker, telegram-bot
- API: 127.0.0.1:8000:8000 only, не 0.0.0.0
- Postgres/Redis: не exposed publicly, internal network only
- Variable substitution из .env
- DEBUG=false, SQL_ECHO=false, RUNTIME_PROVIDER=stub
- Healthchecks для postgres, redis, api

### .env.example

- Все required variables с CHANGE_ME placeholders
- Security comments (never commit .env, chmod 600)
- Категории: Core, Database, Redis, Telegram, API, Production (Caddy/TLS)

### Validation script

- **Файл:** `scripts/deploy/validate-production-templates.sh`
- 9 check categories: file existence, no real tokens, no SQL_ECHO=true, no DEBUG=true, 127.0.0.1 bind, no inline secrets, script syntax, systemd-analyze (soft), docker compose config (soft)
- Soft failures для systemd-analyze/docker compose (SKIP, не FAIL)
- bash strict mode, no root required, no installs, no .env reads

### Documentation

- **docs/deployment.md** — production architecture, two deployment modes (systemd + Docker Compose), env setup, file permissions, systemd/Caddy install steps (MANUAL), startup order, health checks, rollback procedure
- **docs/operations-runbook.md** — start/stop/restart commands, safe restart order, journalctl checks, health monitoring, DB backup/restore, common troubleshooting, "What NOT to Do" table
- **infra/deploy/README.md** — updated to document all deploy templates

## Validation Results

| Component | Result |
|-----------|--------|
| API compileall | ✅ clean |
| Bot compileall | ✅ clean |
| Worker compileall | ✅ clean |
| API ruff | ✅ clean |
| Bot ruff | ✅ clean |
| Worker ruff | ✅ clean |
| API pytest | 401/401 ✅ |
| Bot pytest | 79/79 ✅ |
| Worker pytest | 98/98 ✅ |
| **Total** | **578/578 ✅** |
| Deploy validation | ALL CHECKS PASSED ✅ |

## Changed Files (14)

### MODIFIED (2)
- `apps/api/app/routers/health.py` — enhanced with DB/Redis checks
- `infra/deploy/README.md` — updated to document all templates

### NEW (12)
- `apps/api/tests/test_health.py` — 4 health check tests
- `infra/deploy/Caddyfile` — Caddy reverse proxy template
- `infra/deploy/agentrouter-api.service` — systemd API unit
- `infra/deploy/agentrouter-worker.service` — systemd Worker unit
- `infra/deploy/agentrouter-telegram-bot.service` — systemd Bot unit
- `infra/docker/docker-compose.prod.yml` — production Docker Compose
- `.env.example` — environment variable template
- `scripts/deploy/validate-production-templates.sh` — safety validation
- `docs/deployment.md` — production deployment guide
- `docs/operations-runbook.md` — operations runbook

## Security Confirmation

- ✅ No secrets in any template file
- ✅ No real tokens or credentials
- ✅ No SQL_ECHO=true defaults
- ✅ No DEBUG=true in production configs
- ✅ API binds 127.0.0.1 only
- ✅ No inline secrets in systemd units
- ✅ .env.example uses CHANGE_ME placeholders only
- ✅ Deploy validation script confirms all above

## Out-of-Scope (Deferred)

- Real VPS deploy
- Installing Caddy / enabling systemd services
- Webhook Telegram mode (polling only)
- Production migrations
- CI/CD pipeline
- Log aggregation/rotation beyond journald/Caddy defaults
- Secret scanning hook installation
- gunicorn migration
- Changing DB/Redis architecture

## Memory Checkpoint

- **Memory updated:** yes
- **Files updated:** PROJECT_MEMORY.md, .ai_memory/current_state.md, .ai_memory/_INDEX.md, .ai_memory/tasks/2026-05-08-task-dop03-production-runtime-templates.md
- **Commit hash:** not committed yet (working tree has uncommitted changes)
