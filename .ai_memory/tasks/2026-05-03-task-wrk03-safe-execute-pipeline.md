# Task Summary: WRK-03 — Safe execute pipeline

**Дата:** 2026-05-03  
**Агент:** backend-architect  
**Статус:** ✅ Выполнена

---

## Цель

Реализовать безопасный execute pipeline для worker без реального запуска команд/контейнеров:
- hard gate по статусу `approved`
- policy-валидация команд
- boundary-проверка worktree
- fake sandbox execution
- audit events + redaction

## Что сделано

### Worker: execute pipeline

- `apps/worker/app/tasks/agent_execute.py`
  - вместо stub реализован safe flow:
    1. `GET /tasks/{id}`
    2. проверка `status == approved`
    3. command policy validation
    4. worktree path generation + boundary validation (`.worktrees`)
    5. `PATCH status -> running`
    6. audit `command_started`
    7. fake sandbox run
    8. audit `command_finished` + `file_changed`
    9. `PATCH status -> completed|failed`
    10. audit `task_completed|task_failed`
  - policy violation path: `security_violation` event + status `failed`
  - result payload сохраняется с redacted/truncated stdout/stderr

### Worker services

- `apps/worker/app/services/command_policy.py`
  - allowlist prefixes: pytest/ruff/compileall/git status/git diff
  - denylist: force push/reset hard, docker/compose, alembic, destructive/system/deploy/secrets patterns
  - `CommandPolicyError`

- `apps/worker/app/services/worktree_policy.py`
  - root: `F:\dev\agentrouter\.worktrees`
  - safe naming: `task-<external_id>-<short_uuid>`
  - `resolve()+relative_to()` boundary check
  - `WorktreePolicyError`

- `apps/worker/app/services/redaction.py`
  - redacts token/password/api_key/bearer/authorization/db urls/private key blocks
  - truncates long text with `[TRUNCATED]`

- `apps/worker/app/services/sandbox_runner.py`
  - `SandboxRunner` protocol
  - `FakeSandboxRunner` (deterministic success/failure for tests)
  - `DockerSandboxRunner` skeleton intentionally disabled in WRK-03

### API updates for audit/events + transitions

- `apps/api/app/routers/task_events.py`
  - added `POST /events/tasks/{task_id}/events` for internal/system event writes

- `apps/api/app/schemas/task_event.py`
  - added `TaskEventCreate`

- `apps/api/app/schemas/task.py`
  - updated transition rule: `running -> completed` allowed

## Тесты

- `apps/worker/tests/test_tasks.py`
  - `test_agent_execute_success`
  - `test_agent_execute_status_gate_violation`
  - `test_agent_execute_command_policy_violation`

- `apps/worker/tests/test_execute_security.py`
  - allowlist/denylist
  - not-allowlisted rejection
  - worktree escape block
  - redaction
  - fake sandbox success/failure

## Проверки

- API: `ruff check app` ✅, `pytest tests -v` ✅ (147/147)
- Worker: `ruff check app` ✅, `pytest tests -v` ✅ (35/35)

## Что осталось fake/stub

- Реальный docker sandbox execution (intentionally not used in WRK-03)
- Реальное выполнение shell-команд (заменено fake runner)
- Реальная Telegram отправка из execute flow (не делалась; только через существующий notifier interface/stubs)

## Ограничения соблюдены

- Не запускались docker build/up
- Не запускались deploy/migrations
- Не менялись `.env`/secrets
- Не было подключения к production/staging
