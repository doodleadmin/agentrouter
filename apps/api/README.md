# apps/api — Orchestrator API

## Описание

FastAPI-сервис — центральный контрольный слой системы Agent Mission Control.

## Ответственности

- REST API для всех операций
- Роутинг сообщений: intent → agent → project → risk level
- CRUD для проектов, агентов, задач, approvals
- Memory retrieval (семантический поиск по vault)
- Approval management и audit logging
- Celery integration для фоновых задач

## Запланированная структура

```
apps/api/
├── app/
│   ├── main.py, config.py
│   ├── db/ (base.py, session, migrations/)
│   ├── models/ (project, agent, telegram_topic, task, approval, task_event, memory_document, memory_chunk)
│   ├── routers/ (health, projects, agents, tasks, approvals, memory, runtime, telegram_webhook)
│   ├── services/
│   ├── workers/ (celery_app, queues)
│   ├── integrations/ (telegram, opencode, git, docker)
│   ├── memory/ (indexer, chunker, embedder, retriever)
│   └── security/ (permissions, risk, audit)
├── tests/
├── pyproject.toml
└── Dockerfile
```

## Статус

> Код ещё не создан. Сейчас — стадия планирования и документации.
