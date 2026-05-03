# Task: tg-01-telegram-gateway

Дата: 2026-05-03
Агент: backend-architect
Проект: agentrouter

---

## Постановка задачи
Реализовать TG-01: отдельное приложение Telegram bot gateway (aiogram 3.x), polling-структура для dev, команды `/start`, `/help`, `/projects`, `/agents`, `/tasks`, topic-aware обработка сообщений и создание task через backend API при привязанном topic.

## Риск-уровень
medium

## Статус
completed

---

## Изменённые файлы
- `apps/telegram-bot/README.md`
- `apps/telegram-bot/pyproject.toml`
- `apps/telegram-bot/app/__init__.py`
- `apps/telegram-bot/app/main.py`
- `apps/telegram-bot/app/config.py`
- `apps/telegram-bot/app/bot.py`
- `apps/telegram-bot/app/handlers/__init__.py`
- `apps/telegram-bot/app/handlers/start.py`
- `apps/telegram-bot/app/handlers/messages.py`
- `apps/telegram-bot/app/handlers/commands.py`
- `apps/telegram-bot/app/services/__init__.py`
- `apps/telegram-bot/app/services/api_client.py`
- `apps/telegram-bot/app/services/topic_context.py`
- `apps/telegram-bot/app/keyboards/__init__.py`
- `apps/telegram-bot/tests/conftest.py`
- `apps/telegram-bot/tests/test_topic_context.py`
- `apps/telegram-bot/tests/test_messages.py`
- `apps/telegram-bot/tests/test_commands_rendering.py`
- `PROJECT_MEMORY.md`
- `.ai_memory/current_state.md`
- `.ai_memory/tasks/2026-05-03-task-tg01-telegram-gateway.md`

## Реализовано
- aiogram 3.x gateway приложение в `apps/telegram-bot/`
- Polling mode entrypoint (`app/main.py`) с безопасным guard по токену
- Команды:
  - `/start`
  - `/help`
  - `/projects` (читает `/projects` backend API)
  - `/agents` (читает `/agents` backend API)
  - `/tasks` (читает `/tasks` backend API)
- Обычный текст:
  - проверка привязки topic через backend `/telegram/topics`
  - если topic привязан: создаётся task через `POST /tasks`
  - если не привязан: бот сообщает, что topic не привязан, и предлагает `/bind_topic` позже
- Ответы всегда отправляются в тот же topic через `message_thread_id`

## Проверки
- `python -m compileall app` ✅
- `ruff check app` ✅
- `pytest tests -v` ✅ (8/8)

## Ограничения соблюдены
- polling реально не запускался
- webhook не реализован
- runtime/OpenCode не запускался
- deploy не выполнялся
- `.env/secrets` не менялись
- вне `F:\dev\agentrouter` работа не велась

## Следующие шаги
1. TG-02: `/bind_topic` + routing bridge
2. WRK-01: Celery app + queues
