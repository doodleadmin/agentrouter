# Task Summary: WRK-01 — Celery Worker Skeleton

**Дата:** 2026-05-03
**Агент:** backend-architect
**Статус:** ✅ Выполнена

---

## Цель

Создать worker foundation на Celery: 7 очередей, healthcheck, stub-задачи, retry/backoff, pydantic-settings конфигурация.

## Что сделано

### Структура `apps/worker/`

```
apps/worker/
├── README.md
├── pyproject.toml
├── app/
│   ├── __init__.py
│   ├── main.py            — entrypoint (exposes celery_app for CLI)
│   ├── config.py           — pydantic-settings (broker, retry, concurrency)
│   ├── celery_app.py       — Celery app factory + config
│   ├── queues.py           — 7 queue name constants
│   └── tasks/
│       ├── __init__.py
│       ├── health.py           — healthcheck task
│       ├── telegram_inbound.py — stub: inbound message processing
│       ├── agent_plan.py       — HTTP call to backend /runtime endpoint
│       ├── agent_execute.py    — stub: execution (WRK-03)
│       ├── memory_index.py     — stub: indexing (MEM-03)
│       ├── deploy.py           — staging stub + production BLOCKED
│       └── notifications.py    — stub: notifications
└── tests/
    ├── conftest.py
    ├── test_celery_app.py   — 5 tests (queues, config, serialization)
    ├── test_tasks.py        — 8 tests (all stubs + agent_plan error)
    ├── test_queues.py       — 3 tests (constants)
    └── test_config.py       — 1 test (defaults)
```

### 7 очередей

| Очередь | Назначение | Статус |
|---------|-----------|--------|
| `telegram_inbound` | Входящие сообщения | Stub |
| `agent_plan` | Генерация плана | HTTP call to backend |
| `agent_execute` | Выполнение в sandbox | Stub (WRK-03) |
| `memory_index` | Индексация памяти | Stub (MEM-03) |
| `deploy_staging` | Staging deploy | Stub (DOP-04) |
| `deploy_production` | Production deploy | **Всегда blocked** |
| `notifications` | Уведомления | Stub |

### Конфигурация

- `CELERY_BROKER_URL` — Redis (default: `redis://localhost:6379/1`)
- `CELERY_RESULT_BACKEND` — Redis (default: `redis://localhost:6379/2`)
- `TASK_MAX_RETRIES` — 3
- `TASK_RETRY_BACKOFF` — True
- `WORKER_CONCURRENCY` — 4
- JSON serialization, acks_late, result_expires=3600

### Ключевые решения

1. **agent_plan** делает реальный HTTP call к `POST /runtime/tasks/{task_id}/plan` — это безопасно (только API call)
2. **deploy_production** никогда не выполняет реальные действия — всегда возвращает `blocked`
3. **Retry policy** применяется через `autoretry_for=(Exception,)` + backoff/jitter
4. **healthcheck** не использует retry (max_retries=0)

## Изменённые файлы

- `apps/worker/README.md` — обновлён (был placeholder)
- `apps/worker/pyproject.toml` — новый
- `apps/worker/app/__init__.py` — новый
- `apps/worker/app/main.py` — новый
- `apps/worker/app/config.py` — новый
- `apps/worker/app/celery_app.py` — новый
- `apps/worker/app/queues.py` — новый
- `apps/worker/app/tasks/__init__.py` — новый
- `apps/worker/app/tasks/health.py` — новый
- `apps/worker/app/tasks/telegram_inbound.py` — новый
- `apps/worker/app/tasks/agent_plan.py` — новый
- `apps/worker/app/tasks/agent_execute.py` — новый
- `apps/worker/app/tasks/memory_index.py` — новый
- `apps/worker/app/tasks/deploy.py` — новый
- `apps/worker/app/tasks/notifications.py` — новый
- `apps/worker/tests/conftest.py` — новый
- `apps/worker/tests/test_celery_app.py` — новый
- `apps/worker/tests/test_tasks.py` — новый
- `apps/worker/tests/test_queues.py` — новый
- `apps/worker/tests/test_config.py` — новый
- `PROJECT_MEMORY.md` — обновлён
- `.ai_memory/current_state.md` — обновлён

## Проверки

| Проверка | Результат |
|----------|-----------|
| `python -m compileall app` | ✅ Clean |
| `ruff check app` | ✅ All checks passed |
| `pytest tests -v` (worker) | ✅ 17/17 passed |
| `pytest tests -v` (telegram-bot) | ✅ 14/14 passed |
| `pytest tests -v` (api) | ✅ 46/46 passed |

## Ограничения соблюдены

- ❌ Не запускался celery worker
- ❌ Не запускался docker compose
- ❌ Не делался deploy
- ❌ Не запускался alembic upgrade head
- ❌ Не менялся .env/secrets
- ❌ Не подключался к production/staging
- ❌ Не работал вне `F:\dev\agentrouter`

## Следующие шаги

- **WRK-02:** Plan pipeline — connect agent_plan task to real runtime flow
- **WRK-03:** Execute pipeline — sandbox + worktree + runtime
- **MEM-03:** Memory indexing — replace stub with real parser/embedder
- **DOP-04:** Deploy — replace stubs with real deploy commands
