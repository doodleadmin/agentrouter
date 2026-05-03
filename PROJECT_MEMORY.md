# PROJECT_MEMORY.md — Краткий индекс состояния проекта

> **Это краткая сводка.** Полная память проекта — в `.ai_memory/` (Obsidian-like vault, подключён к MCP).
> Навигация по vault: [.ai_memory/_INDEX.md](.ai_memory/_INDEX.md)

## Текущий статус

**Фаза:** Phase 0 — Подготовка инфраструктуры
**Статус:** WRK-04 REAL docker smoke test (Scenario A) выполнен локально; режим sandbox возвращён в fake.
**Дата последнего обновления:** 2026-05-04
**Project root:** `F:\dev\agentrouter`

## Что сделано

- [x] Спроектирована архитектура системы (3 слоя: Telegram → API → Runtime)
- [x] Определена структура monorepo
- [x] Спроектирована схема БД (8 таблиц)
- [x] Составлен roadmap из 8 фаз
- [x] Создана документация в `docs/`
- [x] Memory vault инициализирован в `.ai_memory/`
- [x] Написаны 4 ADR
- [x] Создан MVP backlog с 25 задачами
- [x] Project root скорректирован: всё в `F:\dev\agentrouter`
- [x] **FND-01:** .gitignore, CHANGELOG, CONTRIBUTING, docs/git-workflow.md
- [x] **FND-02:** FastAPI skeleton (main.py, config.py, /health, pyproject.toml)
- [x] **DOP-01:** dev docker-compose (`infra/docker/docker-compose.yml`)

## Что не сделано

- [x] **FND-03:** SQLAlchemy модели + Alembic baseline миграция (не применялась)
- [x] **BE-01:** CRUD /projects, /agents, /telegram_topics с мягким удалением
- [x] **BE-02:** Tasks + Approvals domain (task lifecycle, approval flow, event audit)
- [x] **TG-01:** Telegram bot gateway (aiogram 3.x, commands + topic-aware task creation)
- [x] **TG-02:** Topic binding + routing bridge (`/bind_topic`, `/unbind_topic`, `/topic_status`)
- [x] **WRK-01:** Celery worker skeleton (7 queues, healthcheck, stubs, retry/backoff)
- [x] **WRK-02:** Plan pipeline (trigger-plan endpoint, agent_plan + notifications tasks, notifier adapter)
- [x] **MEM-01:** Memory provisioning (service, schemas, 5 templates, docs, forbidden content detection)
- [x] **MEM-02:** Memory CRUD API (6 endpoints, policy service, access tiers, secrets guard)
- [x] **DOP-02:** Dockerfiles + sandbox compose (sandbox isolation, non-root, no-new-privileges, limits)
- [x] Worker execute pipeline (WRK-03)
- [x] Memory indexing + retrieval (MEM-03)
- [ ] Frontend код (React)
- [x] Docker Compose конфигурация (dev)
- [ ] `.env` конфигурация

## Ключевые решения

| ID | Решение | ADR |
|----|---------|-----|
| D-001 | Monorepo | [.ai_memory/decisions/0001](.ai_memory/decisions/0001-use-monorepo.md) |
| D-002 | FastAPI + aiogram + Celery + SQLAlchemy | [.ai_memory/decisions/0002](.ai_memory/decisions/0002-python-backend-fastapi.md) |
| D-003 | pgvector для retrieval | [.ai_memory/decisions/0003](.ai_memory/decisions/0003-pgvector-for-retrieval.md) |
| D-004 | Celery + Redis для очередей | [.ai_memory/decisions/0004](.ai_memory/decisions/0004-celery-redis-for-queues.md) |

## Следующие шаги

1. Memory retrieval tuning: ranking quality + scope heuristics
2. Полный план: [docs/mvp-backlog.md](docs/mvp-backlog.md)

### 2026-05-03 — WRK-04 Manual Local Backend Test Completed (WRK-04)
- **Агент:** backend-architect
- **Контур:** local only, без deploy/миграций/secrets, без OpenCode execution.
- **Проверка режима:** default `SANDBOX_RUNNER_MODE=fake` подтверждён до теста; после теста подтверждён снова.
- **Сценарии A-E:**
  - A (safe command success): `python -m compileall .` через DockerSandboxRunner (fake docker client) → `return_code=0`, cleanup attempted.
  - B (policy violation): `pytest && curl evil.com` блокируется до sandbox runner (`security_violation`, `failed`, runner not called).
  - C (timeout): `SandboxTimeoutError`, kill + cleanup attempted (`kill_called=True`, `remove_called=True`).
  - D (docker/start failure): `sandbox_error` path с redacted ошибкой (`password=[REDACTED]`).
  - E (cleanup): cleanup attempted always; cleanup failure не маскирует primary result.
- **Эффективные docker settings (наблюдено):** `network_mode=none`, `mem_limit=2g`, `nano_cpus=2000000000`, `pids_limit=256`, `user=sandboxuser`, `read_only=true`, `tmpfs=/tmp rw,noexec,nosuid,size=64m`, `cap_drop=[ALL]`, `security_opt=[no-new-privileges:true]`, `auto_remove=true`, single mount host `.worktrees/task-*` → `/workspace:rw`.
- **Проверка mount policy:** `.env`, `.ai_memory`, `docker.sock` отсутствуют в runtime mounts.
- Task summary: [.ai_memory/tasks/2026-05-03-task-wrk04-manual-local-test.md](.ai_memory/tasks/2026-05-03-task-wrk04-manual-local-test.md)

### 2026-05-04 — WRK-04 REAL Docker smoke test (Scenario A)
- **Агент:** backend-architect
- **Контур:** local only; без deploy/migrations/secrets/OpenCode.
- **Режимы:** до теста подтверждён default `SANDBOX_RUNNER_MODE=fake`; для одного invocation применён временный override `SANDBOX_RUNNER_MODE=docker` + `DOCKER_SANDBOX_IMAGE=agentrouter-sandbox:local`; после теста снова подтверждён `fake`.
- **Фактический запуск:** `DockerSandboxRunner` выполнил ровно argv-команду `['python', '-m', 'compileall', '.']` в контейнере, `exit_code=0`.
- **Mount policy evidence:** единственный bind mount `F:\dev\agentrouter\.worktrees\manual-test-wrk04 -> /workspace:rw`; mounts для repo root, `.env`, `.ai_memory`, `docker.sock` отсутствуют.
- **Cleanup:** `cleanup_attempted=true`, `cleanup_completed=true`.
- **Примечание к коду:** валидация имени worktree в `DockerSandboxRunner` расширена на префикс `manual-test-` (помимо `task-`) для контролируемых manual smoke tests.
- Task summary: [.ai_memory/tasks/2026-05-03-task-wrk04-real-docker-smoke-test.md](.ai_memory/tasks/2026-05-03-task-wrk04-real-docker-smoke-test.md)

### 2026-05-04 — WRK-04 manual-test hardening
- **Агент:** backend-architect
- **Контур:** local only; без deploy/migrations/secrets/docker.
- **Сделано:**
  - Добавлен `SANDBOX_MANUAL_TEST_MODE: bool = False` в `apps/worker/app/config.py`.
  - В `DockerSandboxRunner.run()` префикс `manual-test-*` теперь разрешён только при `SANDBOX_MANUAL_TEST_MODE=True`.
  - В нормальном режиме (default) разрешён только production-safe префикс `task-<external_id>-<short_uuid>`.
  - Path traversal (выход за `.worktrees`) отклоняется всегда, независимо от режима.
  - `build_worktree_path()` всегда генерирует только `task-*` префикс.
  - Добавлены 5 тестов hardening в `test_sandbox_runner.py`.
  - `FakeSandboxRunner` остаётся default (без изменений, без валидации пути).
  - Реальный Docker не запускался.
- **Проверки:** compileall ✅, ruff ✅, pytest ✅
- Task summary: [.ai_memory/tasks/2026-05-04-task-wrk04-manual-test-hardening.md](.ai_memory/tasks/2026-05-04-task-wrk04-manual-test-hardening.md)
3. Полный план: [docs/mvp-backlog.md](docs/mvp-backlog.md)

## Изменения

### 2026-05-03 — WRK-04 Manual DevOps slice (local compose verification)
- **Агент:** devops-automator
- **Сделано:**
  - Проверен effective config: `docker compose -f infra/docker/sandbox.compose.yml config`
  - Подтверждены security settings sandbox: `read_only`, `cap_drop: ALL`, `no-new-privileges`, `internal` network, `mem/cpu/pids` limits, отсутствие host/docker.sock mount
  - Для manual test создан локальный worktree path: `.worktrees/manual-test-wrk04/sample.py`
- **Ограничения:** image presence check не выполнялся отдельной командой (по условиям разрешены только `compose config` и conditional `docker build`).

### 2026-05-03 — WRK-04 Polish Completed (pre-manual-test hardening)
- **Агент:** backend-architect
- **Закрыты medium/low замечания из post-implementation review:**
  - Добавлены unit-тесты cleanup failure path: cleanup ошибка не маскирует primary success/error.
  - Добавлен отдельный unit-тест Docker unavailable path с проверкой redaction чувствительных деталей.
  - `result_summary` в execute flow теперь динамический по режиму sandbox (`fake`/`docker`), без misleading текста.
  - В docs исправлен счётчик event types: 21 -> 23.
  - Добавлен checklist manual Docker sandbox test в security/deployment policy docs.
- **Дополнительно:**
  - container name sanitation в DockerSandboxRunner для предсказуемых/безопасных имён.
- **Проверки:**
  - Worker: `compileall` ✅, `ruff` ✅, `pytest` ✅ (84/84)
- Task summary: [.ai_memory/tasks/2026-05-03-task-wrk04-polish-pre-manual-test.md](.ai_memory/tasks/2026-05-03-task-wrk04-polish-pre-manual-test.md)

### 2026-05-03 — WRK-04 Completed (DockerSandboxRunner implementation, opt-in)
- **Агент:** backend-architect
- **Закрыты BLOCKING issues B-1..B-4:**
  - **B-1 Mount policy:** удалён статический mount `../../:/workspace:rw` из `infra/docker/sandbox.compose.yml`; runtime mount теперь только validated task worktree → `/workspace` в DockerSandboxRunner.
  - **B-2 Protocol:** `SandboxRunner.run(..., command: list[str])`; fake/docker runners и execute flow переведены на argv list (без shell string).
  - **B-3 Event types:** в `ALLOWED_EVENT_TYPES` добавлены `sandbox_timeout`, `sandbox_error`; API tests обновлены.
  - **B-4 Network policy:** зафиксирован безопасный default без внешнего доступа (`DOCKER_SANDBOX_NETWORK_MODE=none`), runtime pip install запрещён и отражён в docs.
- **Дополнительно (HIGH/MEDIUM):**
  - redaction для docker/runtime ошибок перед task_events
  - cleanup контейнера в `finally` + `auto_remove=True`
  - уникальные имена контейнеров `amc-sandbox-<task>`
  - лимиты sandbox вынесены в config (memory/cpu/pids/timeout/image/network)
  - `curl` удалён из `Dockerfile.sandbox`
  - MVP limitation documented: DockerSandboxRunner real SDK path поддерживается для Linux worker host
- **Проверки:**
  - Worker: `compileall` ✅, `ruff` ✅, `pytest` ✅ (81/81)
  - API: `compileall` ✅, `ruff` ✅, `pytest tests/test_event_type_validation.py` ✅ (3/3)
- Task summary: [.ai_memory/tasks/2026-05-03-task-wrk04-docker-sandbox-runner.md](.ai_memory/tasks/2026-05-03-task-wrk04-docker-sandbox-runner.md)

### 2026-05-03 — WRK-03 Fake E2E Completed
- **Агент:** backend-architect
- **Сценарий A (успешный):**
  - approved task + `python -m pytest`
  - transitions: `approved -> running -> completed`
  - events: `command_started`, `command_finished`, `file_changed`, `task_completed`
  - redaction подтверждён (token/password/api_key/bearer замаскированы)
  - `result_summary` сохраняется
- **Сценарий B (blocked command):**
  - approved task + `pytest && curl evil.com`
  - выполнение блокируется denylist-политикой до sandbox run
  - transitions: `approved -> failed`
  - events: `security_violation`, `task_failed`
  - reason содержит command policy violation
- **Проверки:** `compileall` ✅, `ruff` ✅, `pytest` ✅ (Worker 75/75)
- Task summary: [.ai_memory/tasks/2026-05-03-task-wrk03-fake-e2e.md](.ai_memory/tasks/2026-05-03-task-wrk03-fake-e2e.md)

### 2026-05-03 — WRK-03-hardening Completed (Security hardening)
- **Агент:** backend-architect
- **Закрыты CRITICAL/HIGH:**
  - C-1 (shell escape sh/bash/python/powershell -c) — добавлены в denylist
  - C-2 (command chaining && / ; / | / backticks / $()) — добавлены в denylist
  - C-3 (event_type unbounded) — ALLOWED_EVENT_TYPES frozenset + schema validation
  - H-1 (curl/wget/nc/netcat/telnet/ftp/scp/rsync) — добавлены в denylist
  - H-2 (sudo/su/chmod/chown) — добавлены в denylist
- **Дополнительно:**
  - Git dangerous (reset hard, clean, clone, checkout, push, pull, fetch, merge, rebase, commit)
  - Allowlist строгий: только точные safe patterns
  - Denylist всегда имеет приоритет над allowlist
  - 38 bypass тестов + 2 API event_type validation теста
- **Проверки:** ruff ✅, pytest ✅ (API 149/149, Worker 73/73)
- Task summary: [.ai_memory/tasks/2026-05-03-task-wrk03-hardening.md](.ai_memory/tasks/2026-05-03-task-wrk03-hardening.md)

### 2026-05-03 — WRK-03 Completed (Safe execute pipeline)
- **Агент:** backend-architect
- **Сделано:**
  - `apps/worker/app/tasks/agent_execute.py` переписан со status gate (`approved` only)
  - Добавлены security services:
    - `command_policy.py` (allowlist/denylist)
    - `worktree_policy.py` (boundary validation under `.worktrees`)
    - `redaction.py` (secrets redaction + truncation)
    - `sandbox_runner.py` (`SandboxRunner`, `FakeSandboxRunner`, disabled `DockerSandboxRunner` skeleton)
  - Audit events через API: `command_started`, `command_finished`, `file_changed`, `task_completed`, `task_failed`, `security_violation`
  - API changes:
    - `task_events` router теперь поддерживает `POST /events/tasks/{task_id}/events`
    - `ALLOWED_TRANSITIONS`: добавлен переход `running -> completed`
  - Обновлены/добавлены тесты worker безопасности и execute flow
- **Проверки:**
  - API: `ruff` ✅, `pytest` ✅ (147/147)
  - Worker: `ruff` ✅, `pytest` ✅ (35/35)
- Task summary: [.ai_memory/tasks/2026-05-03-task-wrk03-safe-execute-pipeline.md](.ai_memory/tasks/2026-05-03-task-wrk03-safe-execute-pipeline.md)

### 2026-05-03 — Security Review фиксирован перед WRK-03
- **Агент:** security-engineer
- **Сделано:**
  - Зафиксирован verdict по готовности WRK-03: запуск допустим только при обязательных guardrails
  - Выровнена политика deploy: staging deploy в MVP = `approval_required`
  - Обновлены документы: `docs/security-policy.md`, `docs/deployment-policy.md`
  - Обновлена память: `.ai_memory/current_state.md`, task summary security review
- **Guardrails для WRK-03 (mandatory):**
  - execute только для `task.status=approved`
  - строгая проверка границ worktree (`resolve()` + `relative_to()`)
  - denylist опасных команд (force push, destructive fs/db/system/deploy/migration)
  - обязательные audit events (`command_started`, `command_finished`, `file_changed`, `task_completed/task_failed`)
  - redaction секретов в логах/task_events
- Task summary: [.ai_memory/tasks/2026-05-03-task-security-review-before-wrk03.md](.ai_memory/tasks/2026-05-03-task-security-review-before-wrk03.md)

### 2026-05-03 — DOP-02 Completed (Dockerfiles + sandbox compose)
- **Агент:** devops-automator
- **Сделано:**
  - Добавлены Dockerfiles: `Dockerfile.api`, `Dockerfile.telegram-bot`, `Dockerfile.worker`, `Dockerfile.sandbox`
  - Добавлен `infra/docker/sandbox.compose.yml` для будущего WRK-03
  - Security: non-root users, `no-new-privileges`, `cap_drop: ALL`, `privileged: false`, internal isolated network, resource limits
  - Документация обновлена: `infra/docker/README.md`, `infra/README.md`, `docs/deployment-policy.md`, `docs/security-policy.md`
  - Healthchecks добавлены для всех образов/compose-сервиса
- **Проверки:** `docker compose -f infra/docker/sandbox.compose.yml config` ✅
- Task summary: [.ai_memory/tasks/2026-05-03-task-dop02-dockerfiles-sandbox-compose.md](.ai_memory/tasks/2026-05-03-task-dop02-dockerfiles-sandbox-compose.md)

### 2026-05-03 — MEM-03 Completed (Memory indexing + retrieval)
- **Агент:** backend-architect
- **Сделано:**
  - `memory_chunking_service.py` — heading-aware chunking, fallback split, chunk_index support
  - `memory_embedding_service.py` — deterministic fake embeddings (1536 dim), cosine similarity
  - `memory_indexing_service.py` — vault scan (`.ai_memory/**/*.md`), hash-skip, safe old-chunk replacement, project mapping
  - `memory_retrieval_service.py` — repository protocol + SQLAlchemy repo + top-k ranking
  - `routers/memory.py` — добавлены endpoints `POST /memory/reindex`, `POST /memory/search`
  - `worker/tasks/memory_index.py` — теперь вызывает API `/memory/reindex` (вместо stub)
  - Тесты: `test_memory_chunking.py`, `test_memory_retrieval.py`, расширен `test_memory_router.py`, обновлён worker `test_tasks.py`
- **Проверки:** compileall ✅, ruff ✅, pytest ✅ (API 147/147, Worker 27/27)
- Task summary: [.ai_memory/tasks/2026-05-03-task-mem03-memory-indexing-retrieval.md](.ai_memory/tasks/2026-05-03-task-mem03-memory-indexing-retrieval.md)

### 2026-05-03 — MEM-02 Completed (Memory CRUD API)
- **Агент:** backend-architect
- **Сделано:**
  - `memory_policy_service.py` — path validation, access tiers (FREE/APPROVAL_REQUIRED/FORBIDDEN), secrets guard
  - `memory_service.py` — read_file, write_file (with bypass_approval), append_file, list_files, get_access_tier
  - `routers/memory.py` — 6 endpoints: GET/PUT/POST memory files, provision, access info
  - Schemas обновлены: MemoryFileRead/Write/WriteRequest/ListResult/AccessInfo
  - 76 новых тестов (35 policy + 20 service + 17 router + 4 provisioning adjustments)
- **Проверки:** compileall ✅, ruff ✅, pytest ✅ (140/140 API total)
- Task summary: [.ai_memory/tasks/2026-05-03-task-mem02-memory-crud-api.md](.ai_memory/tasks/2026-05-03-task-mem02-memory-crud-api.md)

### 2026-05-03 — MEM-01 Completed (Memory provisioning)
- **Агент:** knowledge-steward
- **Сделано:**
  - `MemoryProvisioningService` — создаёт 7 файлов памяти проекта (overview, current_state, architecture, decisions, tasks, known_issues, agent_notes)
  - `memory.py` schema — MemoryProvisionRequest/Result/FileResult/ProjectInfo + contains_forbidden_content()
  - 5 шаблонов обновлены/созданы (project-memory, task-summary, agent-notes, ADR, current-state)
  - Vault docs обновлены (README, _INDEX, projects/README)
  - `docs/memory-system.md` — документация для агентов
  - Тесты MEM-01: 12/12 passed
- **Проверки:** compileall ✅, ruff ✅, pytest ✅ (64/64 API total)
- Task summary: [.ai_memory/tasks/2026-05-03-task-mem01-memory-provisioning.md](.ai_memory/tasks/2026-05-03-task-mem01-memory-provisioning.md)

### 2026-05-03 — FND-01 + FND-02 Completed
- **FND-01 (git-workflow-master):** .gitignore, CHANGELOG.md, CONTRIBUTING.md, docs/git-workflow.md
- **FND-02 (backend-architect):** FastAPI skeleton, /health endpoint, pydantic-settings config, pyproject.toml
- Обновлён PROJECT_MEMORY.md, .ai_memory/current_state.md
- Task summary: [.ai_memory/tasks/2026-05-03-task-fnd01-fnd02.md](.ai_memory/tasks/2026-05-03-task-fnd01-fnd02.md)

### 2026-05-03 — FND-03 Completed (DB Foundation)
- **Агент:** backend-architect
- **Сделано:**
  - SQLAlchemy async DB foundation: `app/db/{base,session,enums}.py`
  - Модели 8 таблиц: `Project`, `Agent`, `TelegramTopic`, `Task`, `Approval`, `TaskEvent`, `MemoryDocument`, `MemoryChunk`
  - Alembic в `apps/api/alembic/` (ini, env.py, template, baseline migration)
  - Baseline migration `0001_initial_all_tables.py` включает `CREATE EXTENSION IF NOT EXISTS vector`
- **Ограничения соблюдены:** shell/docker/alembic upgrade/DB connection не запускались
- **Важно:** для `memory_documents(scope, project_id, path)` пока обычный индекс; partial unique index вынесен в follow-up
- Task summary: [.ai_memory/tasks/2026-05-03-task-fnd03-db-foundation.md](.ai_memory/tasks/2026-05-03-task-fnd03-db-foundation.md)

### 2026-05-03 — BE-01 Completed (CRUD endpoints)
- **Агент:** backend-architect
- **Сделано:**
  - Pydantic schemas: `ProjectCreate/Update/Read`, `AgentCreate/Update/Read`, `TelegramTopicCreate/Update/Read`
  - Async services: `ProjectService`, `AgentService`, `TelegramTopicService`
  - Routers: `GET/POST/PATCH/DELETE /projects`, `/agents`, `/telegram/topics`
  - Soft delete: project→status=archived, agent→status=disabled, topic→is_active=False
  - 17 тестов (schema validation + router structure) — все пройдены
- **Проверки:** `compileall` ✅, `ruff` ✅, `pytest` ✅ (17/17)
- Task summary: [.ai_memory/tasks/2026-05-03-task-be01-crud.md](.ai_memory/tasks/2026-05-03-task-be01-crud.md)

### 2026-05-03 — BE-02 Completed (Tasks + Approvals)
- **Агент:** backend-architect
- **Сделано:**
  - `TaskService`: create (auto external_id), status transitions (15 legal), cancel, list/filter, auto event logging
  - `ApprovalService`: create_request, approve, reject (double-decide blocked), list_by_task, event logging
  - `TaskEventService`: append-only create, list_by_task, list_all with filters
  - Routers: 6 task endpoints + 5 approval endpoints + 2 event endpoints
  - Pydantic schemas: TaskCreate/Update/StatusUpdate/Read, ApprovalCreate/DecideIn/Read, TaskEventRead
- **Проверки:** `compileall` ✅, `ruff` ✅, `pytest` ✅ (41/41: 14 tasks + 10 approvals + 17 existing)
- Task summary: [.ai_memory/tasks/2026-05-03-task-be02-approvals.md](.ai_memory/tasks/2026-05-03-task-be02-approvals.md)

### 2026-05-03 — TG-01 Completed (Telegram bot gateway)
- **Агент:** backend-architect
- **Сделано:**
  - Отдельное приложение `apps/telegram-bot/` на aiogram 3.x
  - Polling-режим для dev (без запуска в рамках задачи)
  - Команды: `/start`, `/help`, `/projects`, `/agents`, `/tasks`
  - API client к backend для команд и создания task
  - Topic-aware обработка текста: если topic привязан → создаётся task, если нет → сообщение о непривязке
  - Ответы всегда отправляются в тот же topic через `message_thread_id`
  - Тесты TG-01: 8/8 passed
- **Проверки:** `compileall` ✅, `ruff` ✅, `pytest` ✅ (8/8)
- Task summary: [.ai_memory/tasks/2026-05-03-task-tg01-telegram-gateway.md](.ai_memory/tasks/2026-05-03-task-tg01-telegram-gateway.md)

### 2026-05-03 — TG-02 Completed (Topic binding + routing bridge)
- **Агент:** backend-architect
- **Сделано:**
  - Новые команды: `/bind_topic`, `/unbind_topic`, `/topic_status`
  - Привязка topic по формату `/bind_topic project=<slug> agent=<slug>`
  - Валидация forum-topic контекста (`message_thread_id` обязателен)
  - Soft unbind через deactivate (`DELETE /telegram/topics/{id}`)
  - `topic_status` показывает chat_id, message_thread_id, project_id, agent_id, status
  - Routing bridge обновлён: непривязанный topic → подсказка `/bind_topic`, привязанный topic → `POST /tasks`
  - Роутеры TG-02 зарегистрированы в dispatcher
  - Тесты TG-02 добавлены и пройдены
- **Проверки:** `compileall` ✅, `ruff` ✅, `pytest` ✅ (14/14)
- Task summary: [.ai_memory/tasks/2026-05-03-task-tg02-topic-binding-routing.md](.ai_memory/tasks/2026-05-03-task-tg02-topic-binding-routing.md)

### 2026-05-03 — BE-03 Completed (Runtime adapter, plan-only)
- **Агент:** backend-architect
- **Сделано:**
  - Добавлен runtime adapter слой (`integrations/opencode/*`) с контрактом `OpenCodeClientProtocol` и `StubOpenCodeClient`
  - Добавлен `RuntimeService` с endpoint-флоу plan-only: контекст задачи → генерация плана → сохранение `plan_text`
  - Добавлен endpoint `POST /runtime/tasks/{task_id}/plan`
  - Реализована логика риска:
    - `low` → автоматический переход в `approved`
    - `medium/high/critical` → переход в `waiting_approval` + создание approval request
  - Логируются события: `plan_generated`, `approval_requested`
  - Добавлены тесты BE-03 (`apps/api/tests/test_runtime.py`)
- **Ограничения соблюдены:** никаких runtime/shell/deploy/git/worktree/.env/secrets действий
- **Проверки:** `compileall` ✅, `ruff` ✅, `pytest` ✅ (46/46)
- Task summary: [.ai_memory/tasks/2026-05-03-task-be03-runtime-plan-only.md](.ai_memory/tasks/2026-05-03-task-be03-runtime-plan-only.md)

### 2026-05-03 — WRK-02 Completed (Plan pipeline)
- **Агент:** backend-architect
- **Сделано:**
  - **API:** `POST /tasks/{task_id}/trigger-plan` — валидирует (project_id, agent_id), переводит в `routed`, диспетчеризует Celery `agent_plan`
  - **API:** `integrations/queue.py` — тонкий Celery `send_task` dispatcher (broker-only, без импорта worker кода)
  - **Worker:** `agent_plan` task переписан — вызывает runtime API, получает результат, диспетчеризует `send_notification` с планом
  - **Worker:** `notifications` task переписан — использует `Notifier` adapter pattern
  - **Worker:** `services/notifier.py` — `Notifier` protocol + `TelegramNotifier` (httpx) + `StubNotifier` (testing) + factory
  - **Worker:** `config.py` добавлен `TELEGRAM_BOT_TOKEN`
  - **Telegram bot:** `messages.py` — после создания task вызывает `trigger_plan`, показывает статус pipeline
  - **Telegram bot:** `api_client.py` — добавлен метод `trigger_plan(task_id)`
  - Тесты: API 140/140, Worker 26/26, Telegram bot 15/15 = **181 total**
- **Pipeline flow:** Telegram → POST /tasks → POST /trigger-plan → Celery agent_plan → POST /runtime/plan → Celery notifications → Telegram topic
- **Проверки:** `compileall` ✅, `ruff` ✅, `pytest` ✅ (93/93)
- Task summary: [.ai_memory/tasks/2026-05-03-task-wrk02-plan-pipeline.md](.ai_memory/tasks/2026-05-03-task-wrk02-plan-pipeline.md)

### 2026-05-03 — WRK-01 Completed (Celery worker skeleton)
- **Агент:** backend-architect
- **Сделано:**
  - Отдельное приложение `apps/worker/` на Celery
  - 7 именованных очередей: telegram_inbound, agent_plan, agent_execute, memory_index, deploy_staging, deploy_production, notifications
  - Healthcheck task (`tasks.healthcheck`)
  - Stub-задачи для всех очередей (кроме agent_plan — делает HTTP call to backend)
  - `deploy_production` всегда возвращает blocked/requires_approval
  - Retry/backoff policy через pydantic-settings
  - JSON serializer, acks_late, result expiry
  - Тесты WRK-01: 17/17 passed
- **Проверки:** `compileall` ✅, `ruff` ✅, `pytest` ✅ (17/17)
- Task summary: [.ai_memory/tasks/2026-05-03-task-wrk01-celery-worker.md](.ai_memory/tasks/2026-05-03-task-wrk01-celery-worker.md)

### 2026-05-03 — DOP-01 Completed (Dev docker-compose)
- **Агент:** devops-automator
- **Сделано:** создан `infra/docker/docker-compose.yml` для локальной dev-инфраструктуры
  - `postgres` (`pgvector/pgvector:pg16`)
  - `redis` (`redis:7-alpine`)
  - `api` (локальный запуск FastAPI в контейнере)
  - named volumes: `amc_dev_postgres_data`, `amc_dev_redis_data`
  - healthchecks для всех трёх сервисов
  - isolated bridge network `amc_dev_net`
- **Ограничения соблюдены:** staging/prod не трогались, `.env`/secrets не создавались, shell/deploy не запускались
- Task summary: [.ai_memory/tasks/2026-05-03-task-dop01-dev-docker-compose.md](.ai_memory/tasks/2026-05-03-task-dop01-dev-docker-compose.md)

### 2026-05-03 — Project Root Correction + Memory Sync
- Вся документация перенесена в правильный project root
- `.ai_memory/` заполнен как главный Obsidian vault

### 2026-05-03 — Инициализация проекта
- Создана структура директорий и документация
- Спроектирована архитектура и схема БД
