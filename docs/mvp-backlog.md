# MVP Backlog — Agent Mission Control

Версия: 2.0
Дата: 2026-05-09
Статус: **MVP v1 COMPLETE** (23/23 original tasks)
Project root: `F:\dev\agentrouter`

---

## MVP v1 Completion Status

**Original MVP backlog: 23/23 COMPLETE**

### Evidence

- Tests: API 401/401, Bot 79/79, Worker 98/98 — **Total 578/578 PASS**
- Security chain: SEC-01..SEC-03B — all PASS (live smoke validated)
- Deploy templates: DOP-03 — dry-run validated (ALL CHECKS PASSED)
- Release workflow: DOP-04 — dry-run validated (ALL CHECKS PASSED)
- Memory checkpoints: 87 task logs in `.ai_memory/tasks/`
- **Real production deploy is NOT part of completed MVP evidence**
- Deploy infrastructure is ready for preflight; real deploy not executed

### Original Backlog — Completion Table

| Task ID | Original Scope | Status | Evidence | Notes |
|---------|---------------|--------|----------|-------|
| FND-01 | Repo bootstrap | ✅ COMPLETE | .gitignore, CHANGELOG, CONTRIBUTING | git-workflow-master |
| FND-02 | API skeleton | ✅ COMPLETE | FastAPI + /health + pyproject.toml | backend-architect |
| FND-03 | DB foundation | ✅ COMPLETE | SQLAlchemy models + Alembic 0001 | backend-architect |
| DOP-01 | Dev docker-compose | ✅ COMPLETE | postgres+redis+api compose | devops-automator |
| DOP-02 | Dockerfiles + sandbox | ✅ COMPLETE | 4 Dockerfiles + sandbox compose | devops-automator |
| BE-01 | CRUD endpoints | ✅ COMPLETE | /projects, /agents, /topics | backend-architect |
| BE-02 | Tasks + Approvals | ✅ COMPLETE | 14+10+2 endpoints | backend-architect |
| BE-03 | Runtime adapter (plan-only) | ✅ COMPLETE | OpenCode adapter + /runtime | backend-architect |
| TG-01 | Bot gateway | ✅ COMPLETE | aiogram 3.x + commands | backend-architect |
| TG-02 | Topic binding + routing | ✅ COMPLETE | /bind_topic, routing bridge | backend-architect |
| TG-03 | Approval cards UX | ✅ COMPLETE | Inline keyboards + callbacks | backend-architect |
| MEM-01 | Memory provisioning | ✅ COMPLETE | Service + 5 templates | knowledge-steward |
| MEM-02 | Memory CRUD API | ✅ COMPLETE | 6 endpoints + access tiers | backend-architect |
| MEM-03 | Indexing + retrieval | ✅ COMPLETE | pgvector + /memory/search | backend-architect |
| MEM-04 | Memory checkpoints | ✅ COMPLETE | AGENTS.md rule + runbook | knowledge-steward |
| SEC-01 | Permission engine | ✅ COMPLETE | Fail-closed, 14 actions, 5 endpoints | security-engineer |
| SEC-02 | Audit trail | ✅ COMPLETE | Model + migration + integration + live smoke | security-engineer |
| SEC-03 | Secrets safety | ✅ COMPLETE | Centralized redaction (10 patterns) | security-engineer |
| WRK-01 | Celery worker | ✅ COMPLETE | 7 queues + healthcheck | backend-architect |
| WRK-02 | Plan pipeline | ✅ COMPLETE | trigger-plan → agent_plan → notifications | backend-architect |
| WRK-03 | Execute pipeline (sandbox) | ✅ COMPLETE | Approved-only + command policy | backend-architect |
| DOP-03 | Production runtime templates | ✅ COMPLETE | Caddy + systemd + prod compose + .env.example | studio-orchestrator |
| DOP-04 | Release workflow scripts | ✅ COMPLETE | preflight + release + rollback + smoke | studio-orchestrator |

### Emergent Completed Work (not in original backlog)

These tasks emerged during development and are complete with task logs:

| Task ID | Scope | Status | Notes |
|---------|-------|--------|-------|
| TG-04 | Live integration (5 phases) | ✅ COMPLETE | Security prereqs, HTML fixes, private chat, live E2E |
| TG-05 | Notifications + admin gate (4 phases + closeout) | ✅ COMPLETE | Live notification smoke, admin approve/reject flows |
| TG-06 | Compact callback protocol (3 phases) | ✅ COMPLETE | < 64 bytes, HMAC-signed, live E2E validated |
| BE-04 | Runtime guardrails | ✅ COMPLETE | provider=stub default, fail-closed |
| BE-05 | RealOpenCodeHttpTransport | ✅ COMPLETE | HTTP/SSE + gap closures + hardening |
| BE-06 | OpenCode smoke test | ✅ COMPLETE | Transport compatibility + task creation fix |
| BE-07 | Payload contract alignment | ✅ COMPLETE | OpenCode 1.14.33 native format |
| BE-08 | Session traceability | ✅ COMPLETE | Timeout tuning + real smoke success |
| BE-09 | Worker timeout fix | ✅ COMPLETE | API_TIMEOUT 30→300 |
| BE-10 | Runtime reliability | ✅ COMPLETE | Idempotency + retry + timeout alignment |
| BE-11 | Runbook + scripts | ✅ COMPLETE | Smoke automation + script repair |
| BE-12 | Read-timeout alignment | ✅ COMPLETE | SDK-compatible unbounded read |
| WRK-04 | Docker sandbox runner | ✅ COMPLETE | Opt-in adapter, real docker smoke validated |
| DEV-LINUX-01..01D | Ubuntu 22.04 runtime scripts | ✅ COMPLETE | 10 bash scripts + dry-run fixes |
| WORKER-LINUX-01 | Celery SIGHUP fix | ✅ COMPLETE | Monkey-patch + SIG_IGN |
| DEV-DB-01 | Alembic async/sync fix | ✅ COMPLETE | create_async_engine + safety validation |
| CI-01 | Local validation pipeline | ✅ COMPLETE | compileall + ruff + pytest + safety checks |
| CI-02 | Validation fixes | ✅ COMPLETE | Test reliability improvements |
| INFRA-01 | Dev runtime config drift fix | ✅ COMPLETE | .env.local sourcing + bootstrap-seed |
| INFRA-02 | TG-06 regression live smoke | ✅ COMPLETE | Zero manual workarounds |
| SEC-03B | SQLAlchemy log safety | ✅ COMPLETE | SQL_ECHO decoupled from DEBUG |

### Deferred / Post-MVP

| Item | Status | Notes |
|------|--------|-------|
| Frontend dashboard (React) | ⏸ DEFERRED | v2 |
| PR automation (GitHub/GitLab) | ⏸ DEFERRED | Phase 5 |
| Real production deploy | ⏸ REQUIRES APPROVAL | Templates dry-run validated only |
| Telegram webhook mode | ⏸ DEFERRED | Currently long-polling |
| CI/CD remote pipeline | ⏸ DEFERRED | GitHub Actions / GitLab CI |
| Observability / log rotation | ⏸ DEFERRED | Sentry / Grafana / Prometheus |
| Qdrant migration | ⏸ DEFERRED | Currently pgvector |
| Agent permissions JSONB Phase 3 | ⏸ DEFERRED | API-level enforcement |
| Memory retrieval tuning | ⏸ DEFERRED | Ranking quality + scope heuristics |

---

## MVP v1 Scope (утверждён)

MVP v1 включает этапы: foundation, backend, telegram bot, memory system, worker/task runner, devops, security.
Frontend dashboard и расширенные возможности — в v2.

## Operational Constraints (обязательные для всей v1)

1. Каждый этап выполняется только после отдельного approve.
2. Нельзя создавать production-код без отдельного approve.
3. Нельзя запускать shell-команды без отдельного approve.
4. Нельзя делать deploy.
5. Нельзя создавать или менять `.env` / secrets / tokens.
6. Нельзя запускать миграции.
7. Нельзя подключаться к реальным серверам и production DB.
8. Любые действия с Docker, Alembic, git branch, migration, deploy — только после отдельного approve.
9. Каждый агент после изменений обязан: показать changed files, описать изменения, обновить `PROJECT_MEMORY.md` или `.ai_memory/`, остановиться и ждать approve.
10. Единственный project root: `F:\dev\agentrouter`.
11. Главный vault памяти: `.ai_memory/`. Не создавать `memory/` в корне.

---

## 1. FOUNDATION

### FND-01 — Repo bootstrap и базовые стандарты

| Поле | Значение |
|------|----------|
| **Агент** | git-workflow-master |
| **Цель** | Подготовить репозиторий к разработке |
| **Вход** | `README.md`, `AGENTS.md`, `docs/roadmap.md` |
| **Выход** | `.gitignore`, `CHANGELOG.md` |
| **DoD** | Правила веток `agent/<task-id>`, соглашение по commit/PR |
| **Approve** | Да — git-операции (branch, merge) |

### FND-02 — API skeleton

| Поле | Значение |
|------|----------|
| **Агент** | backend-architect |
| **Цель** | FastAPI каркас с `/health` |
| **Вход** | `docs/architecture.md`, `AGENTS.md` |
| **Выход** | `apps/api/app/main.py`, `config.py`, `pyproject.toml` |
| **DoD** | `/health` → 200 |
| **Approve** | Да — shell-команды, Docker |

### FND-03 — DB foundation

| Поле | Значение |
|------|----------|
| **Агент** | backend-architect |
| **Цель** | SQLAlchemy модели (8 таблиц) + Alembic |
| **Вход** | `docs/database-schema.md` |
| **Выход** | `apps/api/app/models/*`, `apps/api/alembic/*` |
| **DoD** | Модели соответствуют схеме, код миграций написан |
| **Approve** | Да — Alembic, Docker, БД |

---

## 2. BACKEND

### BE-01 — Projects / Agents / Topics CRUD

| Поле | Значение |
|------|----------|
| **Агент** | backend-architect |
| **Цель** | CRUD endpoints |
| **Вход** | `docs/architecture.md`, `docs/database-schema.md` |
| **Выход** | `routers/*`, `services/*`, `schemas/*` |
| **Approve** | Нет (код) |

### BE-02 — Tasks + Approvals domain

| Поле | Значение |
|------|----------|
| **Агент** | backend-architect |
| **Цель** | Жизненный цикл task + approval API |
| **Вход** | `docs/architecture.md`, `docs/security-policy.md` |
| **Выход** | `routers/tasks.py`, `approvals.py`, services |
| **Approve** | Нет (код) |

### BE-03 — Runtime adapter (plan-only)

| Поле | Значение |
|------|----------|
| **Агент** | backend-architect |
| **Цель** | OpenCode adapter plan-only |
| **Вход** | `docs/architecture.md`, `AGENTS.md` |
| **Выход** | `integrations/opencode/*`, `runtime_service.py` |
| **Approve** | Да — подключение к реальному OpenCode |

---

## 3. TELEGRAM BOT

### TG-01 — Bot gateway

| Поле | Значение |
|------|----------|
| **Агент** | backend-architect |
| **Цель** | Приём сообщений + ответ в topic |
| **Вход** | `docs/telegram-flow.md` |
| **Выход** | `apps/telegram-bot/app/main.py`, `handlers/*` |
| **Approve** | Да — запуск бота, real token |

### TG-02 — Topic binding

| Поле | Значение |
|------|----------|
| **Агент** | backend-architect |
| **Цель** | `/bind_topic` + message → task |
| **Выход** | `handlers/bind_topic.py`, `routing_service.py` |
| **Approve** | Да — runtime-тестирование |

### TG-03 — Approval cards UX

| Поле | Значение |
|------|----------|
| **Агент** | backend-architect + security-engineer |
| **Цель** | Inline approve/reject cards |
| **Выход** | `keyboards/approvals.py`, `handlers/approvals.py` |
| **Approve** | Да — тестирование с реальным ботом |

---

## 4. MEMORY SYSTEM

### MEM-01 — Project memory provisioning

| Поле | Значение |
|------|----------|
| **Агент** | knowledge-steward |
| **Цель** | Автосоздание `.ai_memory/projects/<slug>/` |
| **Вход** | `.ai_memory/templates/*`, `docs/memory-system.md` |
| **Approve** | Да — запись в vault |

### MEM-02 — Memory CRUD + access policy

| Поле | Значение |
|------|----------|
| **Агент** | backend-architect |
| **Цель** | API с зонами free/approval/forbidden |
| **Выход** | `routers/memory.py`, `services/memory_service.py` |
| **Approve** | Да — runtime-операции |

### MEM-03 — Indexing + search

| Поле | Значение |
|------|----------|
| **Агент** | backend-architect |
| **Цель** | Parser/chunker/embedder + `/memory/search` |
| **Выход** | `memory/{indexer,chunker,embedder,retriever}.py` |
| **Approve** | Да — embedding API calls |

### MEM-04 — Mandatory memory updates

| Поле | Значение |
|------|----------|
| **Агент** | knowledge-steward |
| **Цель** | Post-task: task summary + current_state |
| **Approve** | Да — запись в реальный vault |

---

## 5. WORKER / TASK RUNNER

### WRK-01 — Celery app + queues

| Поле | Значение |
|------|----------|
| **Агент** | backend-architect |
| **Цель** | 7 очередей |
| **Выход** | `apps/worker/app/main.py`, `celery_app.py` |
| **Approve** | Да — Redis, shell |

### WRK-02 — Plan pipeline

| Поле | Значение |
|------|----------|
| **Агент** | backend-architect |
| **Цель** | created → planning → approval |
| **Approve** | Да — вызов OpenCode |

### WRK-03 — Execute pipeline in sandbox

| Поле | Значение |
|------|----------|
| **Агент** | backend-architect + devops-automator |
| **Цель** | Approved execution через sandbox/worktree |
| **Approve** | **Да (обязательно)** |

---

## 6. DEVOPS

### DOP-01 — Compose: dev / staging / prod

| Поле | Значение |
|------|----------|
| **Агент** | devops-automator |
| **Цель** | 3 compose-файла |
| **Approve** | **Да — Docker, сервер** |

### DOP-02 — Dockerfiles + sandbox image

| Поле | Значение |
|------|----------|
| **Агент** | devops-automator |
| **Цель** | Контейнеризация всех сервисов + sandbox |
| **Approve** | **Да — Docker build/run** |

### DOP-03 — Reverse proxy + systemd

| Поле | Значение |
|------|----------|
| **Агент** | devops-automator |
| **Approve** | **Да — серверные конфигурации** |

### DOP-04 — Safe deploy jobs + rollback

| Поле | Значение |
|------|----------|
| **Агент** | devops-automator + security-engineer |
| **Approve** | **Да — любые deploy** |

---

## 7. SECURITY

### SEC-01 — Permission engine

| Поле | Значение |
|------|----------|
| **Агент** | security-engineer + backend-architect |
| **Цель** | Исполнять policy из `docs/security-policy.md` |
| **Выход** | `apps/api/app/security/*` |

### SEC-02 — Audit trail completeness

| Поле | Значение |
|------|----------|
| **Агент** | security-engineer |
| **Цель** | Полнота `task_events` |

### SEC-03 — Secrets safety controls

| Поле | Значение |
|------|----------|
| **Агент** | security-engineer + knowledge-steward |
| **Цель** | Исключить утечки секретов в memory/logs |

---

## Рекомендуемый порядок

```
FND-01 → FND-02 → FND-03    (foundation)
       ↓
DOP-01 → DOP-02              (dev-инфра)
       ↓
BE-01 → BE-02                (core API)
       ↓
TG-01 → TG-02 → TG-03        (telegram gateway)
       ↓
MEM-01 → MEM-02 → MEM-03 → MEM-04   (memory)
       ↓
SEC-01 → SEC-02 → SEC-03     (security)
       ↓
WRK-01 → WRK-02              (workers plan-only)
       ↓
BE-03                        (OpenCode adapter)
       ↓
WRK-03                       (sandbox execution)
       ↓
DOP-03 → DOP-04              (production env)
```

Каждый блок ждёт approve перед стартом.

---

## v2 (перенесено)

- Frontend dashboard (FE-01..03)
- PR automation (расширенный)
- Qdrant migration path
- Grafana/Prometheus/Sentry

## Блокеры

### Resolved Blockers

| # | Блокер | Resolution |
|---|--------|------------|
| 1 | OpenCode adapter contract | ✅ RESOLVED — BE-07+ native contract alignment with OpenCode 1.14.33 |
| 2 | Approve policy for code-change consistency | ✅ RESOLVED — SEC-01 PermissionEngine fail-closed + admin gate |
| 3 | aiogram location (`apps/telegram-bot` vs `apps/api`) | ✅ RESOLVED — separate `apps/telegram-bot/` package |
| 4 | Embedding provider (OpenAI vs local) | ✅ RESOLVED — deterministic embeddings (MEM-03) |
| 5 | Worker vs API service boundary | ✅ RESOLVED — Celery worker calls API via HTTP |
| 6 | Infra target (один сервер vs staging/prod) | ✅ RESOLVED — systemd + Docker Compose templates |
| 7 | Frontend в v1 или v2 | ✅ RESOLVED — v2 |

### Active Blockers for MVP v1

**None** — all original blockers resolved.

### Active Blockers for Production Deploy

| # | Блокер | Что нужно |
|---|--------|-----------|
| 1 | Real VPS provisioned | Explicit approval for target server |
| 2 | `.env` with real credentials | Explicit approval for secrets |
| 3 | DNS configured | Domain + TLS setup |
| 4 | Alembic migrations run on production DB | Explicit approval for migrations |
