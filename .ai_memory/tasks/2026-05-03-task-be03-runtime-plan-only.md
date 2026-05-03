# Task: be-03-runtime-plan-only

Дата: 2026-05-03
Агент: backend-architect
Проект: agentrouter

---

## Постановка задачи
Реализовать BE-03: runtime adapter в режиме plan-only без реального запуска OpenCode/shell/runtime действий.

## Риск-уровень
medium

## Статус
completed

---

## Изменённые файлы
- `apps/api/app/integrations/__init__.py`
- `apps/api/app/integrations/opencode/__init__.py`
- `apps/api/app/integrations/opencode/client.py`
- `apps/api/app/integrations/opencode/schemas.py`
- `apps/api/app/services/runtime_service.py`
- `apps/api/app/routers/runtime.py`
- `apps/api/app/routers/__init__.py`
- `apps/api/app/main.py`
- `apps/api/app/services/__init__.py`
- `apps/api/tests/test_runtime.py`
- `PROJECT_MEMORY.md`
- `.ai_memory/current_state.md`
- `.ai_memory/tasks/2026-05-03-task-be03-runtime-plan-only.md`

## Что реализовано
1. Добавлен runtime adapter контракт:
   - `OpenCodeClientProtocol`
   - `RuntimePlanContext`
   - `RuntimePlanResult`
2. Добавлен stub-клиент `StubOpenCodeClient`, который генерирует deterministic `plan_text`.
3. Добавлен `RuntimeService.generate_plan_for_task(task_id)`:
   - валидирует task/project/agent контекст
   - ставит task в `planning`
   - генерирует и сохраняет `plan_text`
   - пишет `plan_generated`
   - low-risk → `approved`
   - medium/high/critical → `waiting_approval` + approval request (`approval_requested`)
4. Добавлен endpoint: `POST /runtime/tasks/{task_id}/plan`.

## Runtime adapter architecture
- **Router layer**: `runtime.py` — HTTP endpoint + error mapping (404/422)
- **Service layer**: `runtime_service.py` — orchestration task→plan→status→events→approval
- **Integration layer**: `integrations/opencode/*` — protocol + stub implementation
- **Extensibility**: позже можно заменить `StubOpenCodeClient` на реальный OpenCode SDK/API без изменения router/service контракта.

## Проверки
- `python -m compileall app` ✅
- `ruff check app` ✅
- `pytest tests -v` ✅ (46/46 passed)

## Ограничения соблюдены
- Реальный OpenCode runtime не запускался
- Команды/деплой/git/worktree не выполнялись
- `.env`/secrets не изменялись
- Вне `F:\dev\agentrouter` работа не велась

## Следующие шаги
1. Approve WRK-01: Celery app + queues
2. Approve DOP-02: Dockerfiles + sandbox compose
