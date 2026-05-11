# Agent Mission Control

**Telegram-controlled orchestration platform for AI agents** with FastAPI backend, Celery worker, project memory, approval gates, security audit trail, and deploy workflow.

---

## MVP Status

| Metric | Status |
|--------|--------|
| MVP v1 | **Complete** |
| Original backlog | 23 / 23 items done |
| Emergent tasks | 21 additional items done |
| Test suite | **578 / 578 passing** |
| Task logs indexed | 87 |
| Security issues (CRITICAL / HIGH) | All closed |
| Production deploy | **NOT executed** (dry-run validated only) |

---

## Architecture

```
Telegram Forum Group
       │
       ▼
Telegram Bot Gateway (aiogram 3.x)
       │
       ▼
Orchestrator API (FastAPI + Pydantic v2)
       │
       ├──► PostgreSQL 16 + pgvector (state, retrieval)
       ├──► Redis 7 + Celery (task queue)
       ├──► Security Layer (permissions, audit, redaction)
       └──► Memory Vault (.ai_memory/ — Obsidian-like)
       │
       ▼
Agent Runtime Adapter (OpenCode)
       │
       ▼
Docker Sandbox + Git Worktree
       │
       ▼
Tests / PR / Deploy Pipeline
```

---

## Project Structure

```
agentrouter/
├── apps/
│   ├── api/              ← FastAPI — Orchestrator API
│   │   ├── app/
│   │   │   ├── models/       SQLAlchemy models
│   │   │   ├── routers/      REST endpoints
│   │   │   ├── services/     Business logic
│   │   │   ├── security/     PermissionEngine, AuditService, Redaction
│   │   │   └── memory/       CRUD, search, reindex
│   │   ├── alembic/          DB migrations
│   │   └── tests/            401 tests
│   ├── telegram-bot/     ← aiogram — Telegram Bot Gateway
│   │   ├── app/
│   │   │   ├── handlers/     Message routing, callbacks, approvals
│   │   │   └── keyboards/    Inline approval cards
│   │   └── tests/            79 tests
│   ├── worker/           ← Celery — Background tasks
│   │   ├── app/
│   │   │   ├── jobs/         Plan, execute, complete pipelines
│   │   │   └── pipelines/    Task lifecycle
│   │   └── tests/            98 tests
│   └── web/              ← React — Web Dashboard (future)
├── infra/
│   ├── docker/               Docker Compose + Dockerfiles
│   │   ├── docker-compose.yml        (dev)
│   │   └── docker-compose.prod.yml   (production template)
│   └── deploy/               Production runtime templates
│       ├── Caddyfile
│       ├── agentrouter-api.service
│       ├── agentrouter-worker.service
│       └── agentrouter-telegram-bot.service
├── scripts/
│   ├── deploy/               Release workflow scripts
│   │   ├── preflight.sh
│   │   ├── release.sh
│   │   ├── rollback.sh
│   │   ├── smoke.sh
│   │   └── validate-production-templates.sh
│   └── dev-linux/             Local development helpers
├── .ai_memory/            ← Obsidian-like project memory vault
│   ├── _INDEX.md             Navigation index (87 task logs)
│   ├── current_state.md      Active system status
│   ├── decisions/            Architecture Decision Records
│   ├── tasks/                Task logs
│   └── agents/               Agent profiles
├── docs/                  ← Project documentation
├── .env.example           ← Environment template (CHANGE_ME placeholders)
├── AGENTS.md              ← Agent rules and risk levels
└── PROJECT_MEMORY.md      ← Memory index → .ai_memory/
```

---

## Key Features

### Core
- **Projects / Agents / Tasks / Approvals** — full CRUD via REST API
- **Telegram topic-aware routing** — map forum topics to agents or projects
- **Inline approval cards** — approve/reject dangerous actions directly in Telegram
- **Permission engine** — role-based access with admin-gated approvals

### Security
- **Security audit trail** — append-only event log for all sensitive operations
- **Centralized secrets redaction** — 10 pattern classes (tokens, URLs, keys, etc.)
- **SQL echo decoupled from DEBUG** — no bind-param logging in production
- **Risk levels** — low / medium / high / critical with escalating approval gates

### Memory
- **Obsidian-like vault** (`.ai_memory/`) — long-term project knowledge
- **Memory CRUD** — create, read, update, delete project memory files
- **Semantic search** — pgvector-powered retrieval across indexed content
- **Auto-reindex** — trigger reindex after task completion

### Worker
- **Celery task pipeline** — plan → approve → execute → complete
- **OpenCode runtime adapter** — pluggable agent runtime (stub for dev, OpenCode for production)
- **Git worktree isolation** — each task gets its own branch and worktree

### Deploy
- **Production templates** — Caddy reverse proxy, systemd units, Docker Compose
- **Release workflow** — preflight → release → smoke → rollback scripts
- **Safe defaults** — all scripts default to `DRY_RUN=true`
- **Approval gates** — `CONFIRM_PRODUCTION_DEPLOY`, `CONFIRM_MIGRATIONS`, `CONFIRM_SERVICE_RESTART`

---

## Test Results

| Suite | Tests | Status |
|-------|-------|--------|
| API (FastAPI) | 401 | ✅ PASS |
| Telegram Bot (aiogram) | 79 | ✅ PASS |
| Worker (Celery) | 98 | ✅ PASS |
| **Total** | **578** | **✅ PASS** |

| Validation | Status |
|------------|--------|
| Deploy template validation | ✅ ALL CHECKS PASSED |
| Release workflow dry-run | ✅ PASS |
| Preflight dry-run | ✅ 29 PASS / 3 WARN / 0 FAIL |
| Rollback dry-run | ✅ PASS |
| Negative gate checks | ✅ Release and rollback refused without confirms |

---

## Local Development

### Prerequisites

- Python 3.12+
- Docker + Docker Compose (for PostgreSQL and Redis)
- Git

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/doodleadmin/agentrouter.git
cd agentrouter

# 2. Start PostgreSQL + Redis
docker compose -f infra/docker/docker-compose.yml up -d

# 3. Copy environment template and fill in values
cp .env.example .env.local
# Edit .env.local with your local database credentials and Telegram bot token

# 4. Install API dependencies and run migrations
cd apps/api
pip install -e ".[dev]"
alembic upgrade head

# 5. Run API tests
pytest --tb=short
# Expected: 401 passed

# 6. Run Telegram bot tests
cd ../telegram-bot
pip install -e ".[dev]"
pytest --tb=short
# Expected: 79 passed

# 7. Run Worker tests
cd ../worker
pip install -e ".[dev]"
pytest --tb=short
# Expected: 98 passed
```

> **Note:** The Telegram bot token and database credentials are required in `.env.local` for runtime. Tests use mock fixtures and do not require live services.

---

## Deployment Status

Production templates are **ready and dry-run validated**, but **real production deployment has not been executed**.

| Component | Template Ready | Deployed |
|-----------|---------------|----------|
| Caddy reverse proxy | ✅ | ❌ Not deployed |
| systemd units (API, Worker, Bot) | ✅ | ❌ Not deployed |
| Docker Compose (prod) | ✅ | ❌ Not deployed |
| Release workflow scripts | ✅ | ❌ Not deployed |
| Preflight validation | ✅ PASS | — |
| Smoke tests | ✅ PASS | — |

Real VPS deploy requires:
1. Explicit production approval
2. Real `.env` with actual credentials (never committed)
3. `CONFIRM_PRODUCTION_DEPLOY=yes` gate
4. Successful preflight checks on target server

See: [docs/deployment.md](docs/deployment.md), [docs/release-workflow.md](docs/release-workflow.md)

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend API | Python 3.12+, FastAPI, Pydantic v2 |
| Telegram Bot | aiogram 3.x |
| Database | PostgreSQL 16 + pgvector |
| Task Queue | Redis 7 + Celery |
| ORM | SQLAlchemy 2.x + Alembic |
| Agent Runtime | OpenCode (pluggable adapter) |
| Memory Vault | Obsidian-like `.ai_memory/` + MCP |
| Sandbox | Docker Compose |
| Reverse Proxy | Caddy (template) |
| Frontend | React + Vite + TailwindCSS (planned) |

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System architecture overview |
| [MVP Backlog](docs/mvp-backlog.md) | Task completion status (23/23) |
| [Roadmap](docs/roadmap.md) | Phase progress and post-MVP plans |
| [Database Schema](docs/database-schema.md) | Table definitions and relations |
| [Telegram Flow](docs/telegram-flow.md) | Bot message routing and handlers |
| [Memory System](docs/memory-system.md) | Vault structure and retrieval |
| [Deployment Guide](docs/deployment.md) | Production setup and operations |
| [Operations Runbook](docs/operations-runbook.md) | Start/stop, monitoring, troubleshooting |
| [Release Workflow](docs/release-workflow.md) | Deploy, rollback, approval gates |
| [Deploy Checklist](docs/deploy-checklist.md) | Pre-flight checklist for releases |
| [Security Policy](docs/security-policy.md) | Risk levels, permissions, audit |
| [Agent Roles](docs/agent-roles.md) | Agent responsibilities and boundaries |
| [Local Runner Product Model](docs/local-runner-product-model.md) | Local runner UX and source model |
| [Local Runner Protocol](docs/local-runner-protocol.md) | Runner states, operations, transport draft |
| [Local Runner Security Model](docs/local-runner-security-model.md) | Allowed-root boundary and approval classes |
| [Local Runner API Contract](docs/local-runner-api-contract.md) | Draft endpoints for pairing/jobs/files/commands |
| [Local Runner Roadmap](docs/local-runner-roadmap.md) | Phase plan from design to approved execution |

---

## Security

- **No secrets committed** — `.env` and `.env.local` are in `.gitignore`
- **`.env.example` uses `CHANGE_ME` placeholders** — safe to commit
- **SQL echo is decoupled from DEBUG** — `SQL_ECHO=false` in production prevents bind-param logging
- **DEBUG is `false` by default** in production templates
- **API binds to `127.0.0.1:8000`** — only accessible through Caddy reverse proxy
- **All agent actions are logged** in append-only security audit trail
- **Production deploy requires explicit approval** — multi-gate confirmation

See: [docs/security-policy.md](docs/security-policy.md)

---

## Post-MVP Roadmap

| Next Phase | Goal |
|------------|------|
| Real VPS deploy | Run preflight + release on production server |
| Telegram webhook mode | Switch from long polling to webhook |
| CI/CD pipeline | GitHub Actions for test + deploy |
| Observability | Logging, metrics, health dashboards |
| Frontend dashboard | React Mission Control UI |
| PR automation | Auto-create PRs from agent tasks |
| Memory retrieval tuning | Improve semantic search quality |
| Multi-project support | Manage multiple user projects |

See: [docs/roadmap.md](docs/roadmap.md)

---

## License

Private repository. All rights reserved.
