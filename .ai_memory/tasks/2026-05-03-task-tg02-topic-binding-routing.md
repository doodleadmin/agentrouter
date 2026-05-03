# Task: tg-02-topic-binding-routing

Дата: 2026-05-03
Агент: backend-architect
Проект: agentrouter

---

## Постановка задачи
Реализовать TG-02: команды `/bind_topic`, `/unbind_topic`, `/topic_status` и routing bridge для обычных сообщений (создание task только для привязанных topics).

## Риск-уровень
medium

## Статус
completed

---

## Изменённые файлы
- `apps/telegram-bot/app/services/api_client.py`
- `apps/telegram-bot/app/services/__init__.py`
- `apps/telegram-bot/app/services/topic_binding.py`
- `apps/telegram-bot/app/handlers/bind_topic.py`
- `apps/telegram-bot/app/handlers/unbind_topic.py`
- `apps/telegram-bot/app/handlers/topic_status.py`
- `apps/telegram-bot/app/handlers/messages.py`
- `apps/telegram-bot/app/handlers/__init__.py`
- `apps/telegram-bot/app/bot.py`
- `apps/telegram-bot/tests/test_topic_binding.py`
- `apps/telegram-bot/tests/test_bind_unbind_topic_handlers.py`
- `apps/telegram-bot/tests/test_messages.py`
- `apps/telegram-bot/tests/conftest.py` (import order auto-fix by ruff)
- `PROJECT_MEMORY.md`
- `.ai_memory/current_state.md`
- `.ai_memory/tasks/2026-05-03-task-tg02-topic-binding-routing.md`

## Реализовано
- `/bind_topic project=<project_slug> agent=<agent_slug>`
  - только в forum topic
  - валидация project/agent через backend API
  - create binding или update existing binding (без физического удаления)
- `/unbind_topic`
  - только в forum topic
  - soft deactivate binding через backend delete endpoint
- `/topic_status`
  - показывает chat_id, message_thread_id, project_id, agent_id, status
- Routing bridge (`messages.py`)
  - если topic не привязан: подсказка про `/bind_topic`
  - если привязан: создаётся task через `POST /tasks` с полями
    `title`, `raw_text`, `normalized_text`, `telegram_chat_id`, `telegram_thread_id`, `created_by`, `project_id`, `agent_id`
- В `bot.py` зарегистрированы новые роутеры TG-02

## Проверки
- `python -m compileall app` ✅
- `ruff check app tests` ✅ (после `--fix`)
- `pytest tests -v` ✅ 14/14

## Ограничения соблюдены
- реальный polling не запускался
- webhook не запускался
- deploy не выполнялся
- `.env/secrets` не менялись
- OpenCode runtime не запускался
- работа только в `F:\dev\agentrouter`

## Следующие шаги
1. WRK-01: Celery app + queues
2. BE-03: Runtime adapter (plan-only)
