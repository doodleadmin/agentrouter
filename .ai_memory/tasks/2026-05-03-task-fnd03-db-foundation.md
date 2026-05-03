# Task: fnd-03-db-foundation

Дата: 2026-05-03
Агент: backend-architect
Проект: agentrouter

---

## Постановка задачи
Реализовать FND-03 DB foundation: SQLAlchemy 2 модели, async session/engine, Alembic baseline в `apps/api/alembic/`, миграция с `CREATE EXTENSION IF NOT EXISTS vector`.

## Риск-уровень
medium

## Статус
completed

---

## Изменённые файлы
- `apps/api/app/db/__init__.py`
- `apps/api/app/db/base.py`
- `apps/api/app/db/session.py`
- `apps/api/app/db/enums.py`
- `apps/api/app/models/__init__.py`
- `apps/api/app/models/project.py`
- `apps/api/app/models/agent.py`
- `apps/api/app/models/telegram_topic.py`
- `apps/api/app/models/task.py`
- `apps/api/app/models/approval.py`
- `apps/api/app/models/task_event.py`
- `apps/api/app/models/memory_document.py`
- `apps/api/app/models/memory_chunk.py`
- `apps/api/alembic.ini`
- `apps/api/alembic/env.py`
- `apps/api/alembic/script.py.mako`
- `apps/api/alembic/versions/0001_initial_all_tables.py`
- `PROJECT_MEMORY.md`
- `.ai_memory/current_state.md`
- `.ai_memory/tasks/2026-05-03-task-fnd03-db-foundation.md`

## Выполненные команды
Не применялось (по ограничению: shell-команды не запускались).

## Результаты
- Добавлена SQLAlchemy 2 база с `Mapped[]`/`mapped_column()`.
- Настроены async engine/session через `sqlalchemy.ext.asyncio`.
- Модели реализуют 8 ключевых таблиц из схемы.
- Alembic вынесен в `apps/api/alembic/`.
- `env.py` импортирует `app.models` для регистрации `Base.metadata`.
- Baseline migration включает `CREATE EXTENSION IF NOT EXISTS vector`.
- Для `memory_documents` применён обычный индекс `scope/project_id/path`; partial unique index оставлен на follow-up.

## Ограничения соблюдены
- `main.py` не изменялся
- Docker/compose не создавались
- `.env` и secrets не изменялись
- миграции не применялись
- подключений к БД/серверам не выполнялось

## Следующие шаги
1. Approve BE-01 (CRUD endpoints)
2. Approve DOP-01 (docker compose planning/implementation)
