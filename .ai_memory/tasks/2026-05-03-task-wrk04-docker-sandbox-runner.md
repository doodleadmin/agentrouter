# Task Summary — WRK-04 DockerSandboxRunner (opt-in)

Дата: 2026-05-03  
Агент: backend-architect  
Статус: ✅ Completed

## Цель

Реализовать production-ready `DockerSandboxRunner` adapter (без реального запуска Docker в задаче),
с сохранением `FakeSandboxRunner` как default и закрытием blocking issues B-1..B-4 из security review.

## Что сделано

1. **B-1 Mount policy closed**
   - Удалён статический mount всего репозитория из `infra/docker/sandbox.compose.yml`.
   - Runtime mount в Docker runner теперь только validated task worktree → `/workspace`.

2. **B-2 Protocol closed**
   - `SandboxRunner` переведён на `command: list[str]` (argv-only).
   - `FakeSandboxRunner` адаптирован под list argv.
   - `agent_execute` теперь валидирует command policy на строке и затем парсит argv через `shlex.split`.

3. **B-3 Event types closed**
   - В `ALLOWED_EVENT_TYPES` добавлены `sandbox_timeout`, `sandbox_error`.
   - Добавлены API-тесты на приём новых event types.

4. **B-4 Network policy closed**
   - В worker config добавлен `DOCKER_SANDBOX_NETWORK_MODE` со значением по умолчанию `none`.
   - Документировано: runtime `pip install` в sandbox запрещён; зависимости предустанавливаются в `Dockerfile.sandbox`.

5. **HIGH/MEDIUM mitigations**
   - Redaction для docker/runtime ошибок перед записью в task_events.
   - Cleanup контейнера через `finally` + `auto_remove=True`.
   - Уникальное имя контейнера: `amc-sandbox-<task>`.
   - Лимиты sandbox вынесены в config (`timeout`, `memory`, `cpu`, `pids`, `image`, `network`).
   - Убран `curl` из `Dockerfile.sandbox`.
   - MVP limitation documented: реальный DockerSandboxRunner поддерживается на Linux worker host.

## Изменённые файлы

- `apps/worker/app/services/sandbox_runner.py`
- `apps/worker/app/config.py`
- `apps/worker/app/tasks/agent_execute.py`
- `apps/worker/tests/test_sandbox_runner.py` (new)
- `apps/worker/tests/test_execute_e2e_fake.py`
- `apps/worker/tests/test_execute_security.py`
- `apps/worker/tests/test_tasks.py`
- `apps/api/app/schemas/task_event.py`
- `apps/api/tests/test_event_type_validation.py`
- `infra/docker/sandbox.compose.yml`
- `infra/docker/Dockerfile.sandbox`
- `docs/security-policy.md`
- `docs/deployment-policy.md`
- `PROJECT_MEMORY.md`
- `.ai_memory/current_state.md`
- `.ai_memory/_INDEX.md`

## Проверки

- Worker:
  - `python -m compileall app` ✅
  - `ruff check app` ✅
  - `pytest tests -v` ✅ (81/81)
- API:
  - `python -m compileall app` ✅
  - `ruff check app` ✅
  - `pytest tests/test_event_type_validation.py -v` ✅ (3/3)

## Ограничения / Важно

- `FakeSandboxRunner` остаётся default (`SANDBOX_RUNNER_MODE=fake`).
- `DockerSandboxRunner` — opt-in (`SANDBOX_RUNNER_MODE=docker`).
- В этой задаче **реальный Docker не запускался**.
