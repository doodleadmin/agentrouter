# MVP Backlog — Agent Mission Control

Версия: 1.0
Дата: 2026-05-03
Статус: **APPROVED** (v1 scope)
Project root: `F:\dev\agentrouter`

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

| # | Блокер | Влияние |
|---|--------|---------|
| 1 | OpenCode adapter contract | BE-03, WRK-03 |
| 2 | Approve policy for code-change consistency | BE-02, SEC-01 |
| 3 | aiogram location (`apps/telegram-bot` vs `apps/api`) | TG-01..03 |
| 4 | Embedding provider (OpenAI vs local) | MEM-03 |
| 5 | Worker vs API service boundary | WRK-01..03 |
| 6 | Infra target (один сервер vs staging/prod) | DOP-01..04 |
| 7 | Frontend в v1 или v2 | Решено: v2 |
