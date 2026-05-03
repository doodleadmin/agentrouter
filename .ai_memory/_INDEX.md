# _INDEX.md — Навигация по vault

> Автоматический индекс. Обновляется при provisioning и после задач.

---

## Структура

| Раздел | Путь | Описание |
|--------|------|----------|
| Правила | [README.md](README.md) | Правила vault |
| Глобальный статус | [current_state.md](current_state.md) | Текущий статус системы |
| Пайплайн | [agent_mission_control_pipeline.md](agent_mission_control_pipeline.md) | Полный маршрут реализации |
| Проекты | [projects/](projects/) | Память по проектам |
| Агенты | [agents/](agents/) | Профили агентов |
| Задачи | [tasks/](tasks/) | Логи задач |
| Решения | [decisions/](decisions/) | Архитектурные решения (ADR) |
| Шаблоны | [templates/](templates/) | Шаблоны документов |

---

## Счётчики

| Категория | Количество |
|-----------|-----------|
| **Проекты** | 0 |
| **Агенты (профили)** | 0 |
| **ADR** | 4 |
| **Task logs** | 28 |
| **Шаблоны** | 5 |

---

## Зарегистрированные проекты

*Пока нет зарегистрированных проектов.*

---

## Агенты

| Агент | Профиль памяти |
|-------|---------------|
| backend-architect | — |
| frontend-developer | — |
| devops-automator | — |
| explore | — |
| knowledge-steward | — |
| security-engineer | — |
| git-workflow-master | — |
| reality-checker | — |
| studio-orchestrator | — |

---

## ADR

| ID | Название | Файл |
|----|----------|------|
| 0001 | Use Monorepo | [0001-use-monorepo.md](decisions/0001-use-monorepo.md) |
| 0002 | Python Backend (FastAPI) | [0002-python-backend-fastapi.md](decisions/0002-python-backend-fastapi.md) |
| 0003 | pgvector for Retrieval | [0003-pgvector-for-retrieval.md](decisions/0003-pgvector-for-retrieval.md) |
| 0004 | Celery + Redis for Queues | [0004-celery-redis-for-queues.md](decisions/0004-celery-redis-for-queues.md) |

---

## Task Logs

| Файл | Задача |
|------|--------|
| [2026-05-03-task-fnd01-fnd02.md](tasks/2026-05-03-task-fnd01-fnd02.md) | FND-01 + FND-02 |
| [2026-05-03-task-fnd03-db-foundation.md](tasks/2026-05-03-task-fnd03-db-foundation.md) | FND-03 |
| [2026-05-03-task-fnd03-fix.md](tasks/2026-05-03-task-fnd03-fix.md) | FND-03 fix |
| [2026-05-03-task-dop01-dev-docker-compose.md](tasks/2026-05-03-task-dop01-dev-docker-compose.md) | DOP-01 |
| [2026-05-03-task-dop01-check.md](tasks/2026-05-03-task-dop01-check.md) | DOP-01 check |
| [2026-05-03-task-be01-crud.md](tasks/2026-05-03-task-be01-crud.md) | BE-01 |
| [2026-05-03-task-be02-approvals.md](tasks/2026-05-03-task-be02-approvals.md) | BE-02 |
| [2026-05-03-task-tg01-telegram-gateway.md](tasks/2026-05-03-task-tg01-telegram-gateway.md) | TG-01 |
| [2026-05-03-task-tg02-topic-binding-routing.md](tasks/2026-05-03-task-tg02-topic-binding-routing.md) | TG-02 |
| [2026-05-03-task-be03-runtime-plan-only.md](tasks/2026-05-03-task-be03-runtime-plan-only.md) | BE-03 |
| [2026-05-03-task-wrk01-celery-worker.md](tasks/2026-05-03-task-wrk01-celery-worker.md) | WRK-01 |
| [2026-05-03-task-wrk02-plan-pipeline.md](tasks/2026-05-03-task-wrk02-plan-pipeline.md) | WRK-02 |
| [2026-05-03-task-mem01-memory-provisioning.md](tasks/2026-05-03-task-mem01-memory-provisioning.md) | MEM-01 |
| [2026-05-03-task-mem02-memory-crud-api.md](tasks/2026-05-03-task-mem02-memory-crud-api.md) | MEM-02 |
| [2026-05-03-task-mem03-memory-indexing-retrieval.md](tasks/2026-05-03-task-mem03-memory-indexing-retrieval.md) | MEM-03 |
| [2026-05-03-task-dop02-dockerfiles-sandbox-compose.md](tasks/2026-05-03-task-dop02-dockerfiles-sandbox-compose.md) | DOP-02 |
| [2026-05-03-task-security-review-before-wrk03.md](tasks/2026-05-03-task-security-review-before-wrk03.md) | Security review before WRK-03 |
| [2026-05-03-task-wrk03-safe-execute-pipeline.md](tasks/2026-05-03-task-wrk03-safe-execute-pipeline.md) | WRK-03 |
| [2026-05-03-task-wrk03-hardening.md](tasks/2026-05-03-task-wrk03-hardening.md) | WRK-03 hardening |
| [2026-05-03-task-wrk03-fake-e2e.md](tasks/2026-05-03-task-wrk03-fake-e2e.md) | WRK-03 fake E2E |
| [2026-05-03-task-wrk04-docker-sandbox-runner.md](tasks/2026-05-03-task-wrk04-docker-sandbox-runner.md) | WRK-04 |
| [2026-05-03-task-wrk04-polish-pre-manual-test.md](tasks/2026-05-03-task-wrk04-polish-pre-manual-test.md) | WRK-04 polish |
| [2026-05-03-task-wrk04-manual-local-test.md](tasks/2026-05-03-task-wrk04-manual-local-test.md) | WRK-04 manual local test |
| [2026-05-03-task-wrk04-real-docker-smoke-test.md](tasks/2026-05-03-task-wrk04-real-docker-smoke-test.md) | WRK-04 real docker smoke test |
| [2026-05-04-task-wrk04-manual-test-hardening.md](tasks/2026-05-04-task-wrk04-manual-test-hardening.md) | WRK-04 manual-test hardening |
| [2026-05-04-task-be04-runtime-guardrails.md](tasks/2026-05-04-task-be04-runtime-guardrails.md) | BE-04 runtime guardrails |
| [2026-05-04-task-be04-review-blockers-fix.md](tasks/2026-05-04-task-be04-review-blockers-fix.md) | BE-04 review blockers fix |
| [2026-05-04-task-be04-transport-hardening.md](tasks/2026-05-04-task-be04-transport-hardening.md) | BE-04 transport hardening |

---

## Шаблоны

| Шаблон | Файл |
|--------|------|
| Project Memory (7 файлов) | [project-memory-template.md](templates/project-memory-template.md) |
| Task Summary | [task-summary-template.md](templates/task-summary-template.md) |
| Agent Notes | [agent-notes-template.md](templates/agent-notes-template.md) |
| ADR | [adr-template.md](templates/adr-template.md) |
| Current State | [current-state-template.md](templates/current-state-template.md) |
