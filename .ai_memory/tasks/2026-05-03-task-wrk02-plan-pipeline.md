# Task Summary: WRK-02 — Plan Pipeline

**Дата:** 2026-05-03
**Агент:** backend-architect
**Статус:** ✅ Выполнена

---

## Цель

Соединить Telegram bot → Backend API → Celery worker → Runtime adapter → Notifications в единый pipeline генерации планов.

## Что сделано

### Pipeline flow

```
Telegram message (bound topic)
    → POST /tasks (create)
    → POST /tasks/{id}/trigger-plan (validate + dispatch)
    → Celery agent_plan queue
    → Worker: POST /runtime/tasks/{id}/plan (generate plan)
    → Worker: fetch task for chat_id/thread_id
    → Worker: dispatch Celery notifications queue
    → Notifier adapter: send to Telegram topic
```

### Изменённые файлы

**API (`apps/api/`):**
- `app/integrations/queue.py` — **новый**: тонкий Celery `send_task` dispatcher
- `app/routers/tasks.py` — **изменён**: добавлен `POST /tasks/{task_id}/trigger-plan` (202 Accepted)
- `tests/test_pipeline.py` — **новый**: 6 тестов (trigger-plan success, event, validation, 404, full pipeline)

**Worker (`apps/worker/`):**
- `app/services/__init__.py` — **новый**: services package
- `app/services/notifier.py` — **новый**: `Notifier` protocol + `TelegramNotifier` (httpx) + `StubNotifier` (testing) + factory
- `app/tasks/agent_plan.py` — **переписан**: вызывает runtime API, диспетчеризует notification
- `app/tasks/notifications.py` — **переписан**: использует Notifier adapter
- `app/config.py` — **изменён**: добавлен `TELEGRAM_BOT_TOKEN`
- `tests/test_notifier.py` — **новый**: 3 теста (stub records, returns ok, Telegram init)
- `tests/test_agent_plan_pipeline.py` — **новый**: 6 тестов (format messages, dispatch, no chat_id)
- `tests/test_tasks.py` — **обновлён**: 8 тестов (добавлены notification tests с StubNotifier)

**Telegram bot (`apps/telegram-bot/`):**
- `app/handlers/messages.py` — **изменён**: после создания task вызывает `trigger_plan`, показывает статус pipeline
- `app/services/api_client.py` — **изменён**: добавлен метод `trigger_plan(task_id)`
- `tests/test_messages.py` — **обновлён**: 4 теста (unbound, bound+plan, plan fails gracefully)

### API endpoint

```
POST /tasks/{task_id}/trigger-plan  →  202 Accepted
```

- Валидирует: task существует, project_id и agent_id заданы
- Переводит статус: `created` → `routed`
- Создаёт event: `plan_triggered`
- Диспетчеризует: `tasks.agent_plan` в Celery queue `agent_plan`

### Notifier adapter

```python
class Notifier(Protocol):
    def send(self, chat_id: int, thread_id: int | None, text: str) -> dict: ...

class TelegramNotifier:  # real Bot API via httpx
class StubNotifier:      # records calls, for testing
```

Factory `get_notifier()` возвращает `TelegramNotifier` если `TELEGRAM_BOT_TOKEN` задан, иначе `StubNotifier`.

## Проверки

| Проверка | Результат |
|----------|-----------|
| `compileall` (api) | ✅ Clean |
| `compileall` (worker) | ✅ Clean |
| `compileall` (telegram-bot) | ✅ Clean |
| `ruff` (all 3) | ✅ All checks passed |
| `pytest` (api) | ✅ 52/52 |
| `pytest` (worker) | ✅ 26/26 |
| `pytest` (telegram-bot) | ✅ 15/15 |
| **Total** | **93/93** |

## Ограничения соблюдены

- ❌ Не запускался Celery worker
- ❌ Не запускался Telegram polling
- ❌ Не делался deploy
- ❌ Не менялся .env/secrets
- ❌ Не подключался к production/staging
- ❌ Не работал вне `F:\dev\agentrouter`

## Следующие шаги

- **WRK-03:** Execute pipeline — git worktree + Docker sandbox + runtime execution
- **MEM-01:** Memory provisioning — vault indexer + retrieval API
- **DOP-02:** Dockerfiles + sandbox compose for all services
