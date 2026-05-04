# Task Summary — BE-06 task creation fix

Date: 2026-05-04
Agent: backend-architect
Scope: `F:\dev\agentrouter`

## Problem statement
- В API наблюдались две связанные проблемы:
  1) успешные POST могли не персиститься стабильно (non-persisting writes) из-за некорректной границы транзакции в request scope;
  2) при невалидных FK ссылках в task creation возникал внутренний `500` вместо безопасной валидационной ошибки.

## Implementation
- Введена корректная transaction boundary для request lifecycle:
  - `commit` при успехе;
  - `rollback` при исключении;
  - закрытие session в рамках context manager.
- Добавлен безопасный mapping `IntegrityError`:
  - FK violation (`23503`) -> `422 Invalid project_id or agent_id reference`;
  - прочие unique/integrity conflicts -> `409 constraint conflict/violation`.
- В create-роутах добавлен явный `rollback()` на ветке `IntegrityError`, чтобы shared test session оставалась в консистентном состоянии после неуспешной записи.

## Files changed
- `apps/api/app/db/session.py`
- `apps/api/app/routers/projects.py`
- `apps/api/app/routers/agents.py`
- `apps/api/app/routers/tasks.py`
- `apps/api/tests/test_runtime_be06_task_creation_fix.py`

## Test outcomes
- Targeted tests: passed (включая persistence после POST, FK mapping и rollback-поведение).
- Full suite note: возможна нестабильность в среде при конкурентных fixture/DB reset сценариях; в рамках фикса подтверждён зелёный targeted прогон.

## Safety constraints respected
- Реальный OpenCode runtime/server не запускался.
- `.env` не изменялся.
- Миграции/деплой не выполнялись.
