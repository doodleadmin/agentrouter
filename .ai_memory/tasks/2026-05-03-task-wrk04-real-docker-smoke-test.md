# WRK-04 — REAL Docker Smoke Test (Scenario A)

Дата: 2026-05-04  
Агент: backend-architect  
Риск: low (local-only smoke)

## Scope
- Проверить, что `DockerSandboxRunner` реально запускает **одну** безопасную команду в контейнере.
- Команда: `['python', '-m', 'compileall', '.']`.
- Worktree: `F:\dev\agentrouter\.worktrees\manual-test-wrk04`.

## Ограничения (соблюдены)
- Только локально, без deploy/staging/prod.
- Без миграций БД.
- Без изменений `.env`/секретов.
- Без OpenCode execution.
- Без git push/pull/clone/fetch.
- Без shell-escape (`sh -c`/`bash -c`/`cmd`/`powershell`), без network/exfiltration tooling.

## Что выполнено
1. Подтверждён default mode:
   - `SANDBOX_RUNNER_MODE=fake` (до теста).
2. Для одного запуска задан временный override в процессе вызова:
   - `SANDBOX_RUNNER_MODE=docker`
   - `DOCKER_SANDBOX_IMAGE=agentrouter-sandbox:local`
   - `DOCKER_SANDBOX_NETWORK_MODE=none`
3. Выполнен реальный запуск контейнера через `DockerSandboxRunner` (CLI docker client adapter).
4. Подтверждено:
   - container started: `true`
   - command executed: `['python', '-m', 'compileall', '.']`
   - exit_code: `0`
   - redaction path applied to stdout/stderr: `true`
   - cleanup attempted/completed: `true/true`
   - mounts: single bind mount `manual-test-wrk04 -> /workspace:rw`
   - forbidden mounts absent: repo root, `.env`, `.ai_memory`, `docker.sock`
5. После теста подтверждён возврат режима:
   - `SANDBOX_RUNNER_MODE=fake`.

## Наблюдаемые docker settings
- image: `agentrouter-sandbox:local`
- network_mode: `none`
- working_dir: `/workspace`
- mem_limit: `2g`
- cpu: `2.0`
- pids_limit: `256`
- read_only: `true`
- tmpfs: `/tmp:rw,noexec,nosuid,size=64m`
- user: `sandboxuser`
- security_opt: `no-new-privileges:true`
- cap_drop: `ALL`
- auto_remove: `true`

## Изменения в коде для сценария manual-test
- `apps/worker/app/services/sandbox_runner.py`
  - валидация имени worktree расширена: разрешён префикс `manual-test-` (в дополнение к `task-`) для контролируемых manual smoke tests.

## Проверка
- `python -m pytest tests/test_sandbox_runner.py` → `7 passed`
