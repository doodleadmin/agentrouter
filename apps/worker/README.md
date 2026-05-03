# apps/worker — Celery Worker

## Назначение

Celery worker — фоновое выполнение задач для Agent Mission Control.

WRK-01 реализует skeleton:
- 7 именованных очередей
- Healthcheck task
- Stub-задачи для всех очередей
- Retry/backoff policy
- pydantic-settings конфигурация

## Структура

```text
apps/worker/
├── app/
│   ├── __init__.py
│   ├── main.py            — entrypoint (exposes celery_app)
│   ├── config.py           — pydantic-settings
│   ├── celery_app.py       — Celery app factory + config
│   ├── queues.py           — queue name constants
│   └── tasks/
│       ├── __init__.py
│       ├── health.py           — healthcheck task
│       ├── telegram_inbound.py — stub: inbound message processing
│       ├── agent_plan.py       — HTTP call to backend /runtime endpoint
│       ├── agent_execute.py    — stub: task execution (WRK-03)
│       ├── memory_index.py     — stub: memory indexing (MEM-03)
│       ├── deploy.py           — deploy_staging (stub) + deploy_production (blocked)
│       └── notifications.py    — stub: notifications
└── tests/
    ├── conftest.py
    ├── test_celery_app.py
    ├── test_tasks.py
    ├── test_queues.py
    └── test_config.py
```

## Очереди

| Очередь | Назначение | Статус WRK-01 |
|---------|-----------|---------------|
| `telegram_inbound` | Обработка входящих сообщений | Stub |
| `agent_plan` | Генерация плана агентом | HTTP call to backend |
| `agent_execute` | Выполнение задачи в sandbox | Stub (WRK-03) |
| `memory_index` | Индексация памяти | Stub (MEM-03) |
| `deploy_staging` | Staging deploy | Stub (DOP-04) |
| `deploy_production` | Production deploy | **Blocked** (всегда) |
| `notifications` | Уведомления | Stub |

## Запуск (после отдельного approve)

```bash
# Все очереди
celery -A app.celery_app worker --loglevel=info

# Только конкретные очереди
celery -A app.celery_app worker --loglevel=info -Q telegram_inbound,agent_plan
```

## Что НЕ делает WRK-01

- Не запускает реальный OpenCode runtime
- Не создаёт git worktree
- Не запускает Docker sandbox
- Не делает deploy
- Не подключается к production/staging
- deploy_production всегда возвращает blocked

## Зависимости от других задач

- WRK-02: plan pipeline (будет использовать agent_plan с реальным runtime)
- WRK-03: execute pipeline (agent_execute + sandbox + worktree)
- MEM-03: memory indexing (memory_index с реальным парсером/embedder)
- DOP-04: deploy (deploy_staging/production с реальными командами)
