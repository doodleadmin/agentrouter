# Task: be-02-tasks-approvals

Дата: 2026-05-03
Агент: backend-architect
Проект: agentrouter

---

## Постановка задачи
BE-02: Tasks + Approvals domain. Реализовать task lifecycle (created → completed/cancelled), approval flow, event audit trail.

## Риск-уровень
low

## Статус
completed

---

## Изменённые файлы

### Созданные (9):
- `apps/api/app/schemas/task.py` — TaskCreate, TaskUpdate, TaskStatusUpdate, TaskRead, ALLOWED_TRANSITIONS
- `apps/api/app/schemas/approval.py` — ApprovalCreate, ApprovalDecideIn, ApprovalRead
- `apps/api/app/schemas/task_event.py` — TaskEventRead (immutable)
- `apps/api/app/services/task_service.py` — TaskService (create, update, status transitions, cancel, list)
- `apps/api/app/services/approval_service.py` — ApprovalService (create, approve, reject, list_by_task)
- `apps/api/app/services/task_event_service.py` — TaskEventService (create, list_by_task, list_all)
- `apps/api/app/routers/tasks.py` — 6 endpoints (prefix /tasks)
- `apps/api/app/routers/approvals.py` — 5 endpoints (prefix /approvals)
- `apps/api/app/routers/task_events.py` — 2 endpoints (prefix /events)

### Изменённые (7):
- `apps/api/app/routers/__init__.py` — added tasks, approvals, task_events exports
- `apps/api/app/main.py` — include 3 new routers
- `apps/api/app/services/__init__.py` — added TaskService, ApprovalService, TaskEventService
- `apps/api/tests/conftest.py` — NullPool + fresh connection per test
- `apps/api/tests/test_tasks.py` — 14 tests
- `apps/api/tests/test_approvals.py` — 11 tests (includes task creation fixture)
- `PROJECT_MEMORY.md`, `.ai_memory/current_state.md`

---

## Endpoints (13 total, all implemented)

### Tasks (6)
- `POST /tasks` — create task (auto external_id: task-0001, task-0002, …)
- `GET /tasks` — list tasks (optional: status, project_id, agent_id, risk_level)
- `GET /tasks/{id}` — get task by id
- `PATCH /tasks/{id}` — update task fields (title, text, metadata)
- `PATCH /tasks/{id}/status` — transition status (validated against ALLOWED_TRANSITIONS)
- `POST /tasks/{id}/cancel` — cancel task (idempotent)

### Approvals (5)
- `POST /approvals/tasks/{id}/approvals` — create approval request
- `GET /approvals/tasks/{id}/approvals` — list approvals for task
- `GET /approvals/{id}` — get approval by id
- `POST /approvals/{id}/approve` — approve (blocks double-decide)
- `POST /approvals/{id}/reject` — reject (blocks double-decide)

### Events (2)
- `GET /events` — list all events (optional: task_id, event_type)
- `GET /events/tasks/{id}/events` — list events for specific task

---

## Task Lifecycle

```
created → routed → planning → waiting_approval → approved → running
    → tests_running → pr_created → deploying_staging → deploying_production → completed
```
Any status → cancelled/failed (legal from any non-terminal state).

13 statuses with ~15 legal transitions validated in service layer.

## Approval Lifecycle

```
pending → approved  (writes task_event)
pending → rejected  (writes task_event)
```
- Double-approve/reject blocked (ValueError)
- Approval payload records action type (deploy_production, run_migration, change_env, delete_files, restart_services)
- Action itself NOT performed — only approval state is managed

## Task Events

- Immutable: create-only, no update/delete
- Auto-logged on: task creation, status transitions, approval decisions

---

## Проверки

| Команда | Результат |
|---------|-----------|
| `compileall app` | ✅ 19 файлов |
| `ruff check` | ✅ passed |
| `pytest tests -v` | ✅ 41/41 (14 tasks + 10 approvals + 17 existing schema/router tests) |

---

## Ограничения соблюдены
- Shell-команды (кроме проверок) не запускались
- Миграции не применялись
- Deploy не выполнялся
- `.env`/secrets не трогались
- Production/staging не подключались

## Следующие шаги
1. Approve TG-01: backend-architect — Telegram bot gateway + webhook
2. Approve SEC-01: security-engineer — permission engine + risk enforcement
