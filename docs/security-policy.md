# Политика безопасности — Agent Mission Control

Версия: 1.0
Дата: 2026-05-03

## Принципы

1. **Least privilege** — агент имеет минимальные права для выполнения задачи
2. **Approval required** — опасные действия требуют подтверждения
3. **Audit everything** — каждое действие логируется
4. **Sandbox isolation** — код выполняется в изолированном контейнере
5. **No secrets exposure** — агенты не видят production secrets

## Уровни риска

| Уровень | Описание | Примеры | Требует approve |
|---------|----------|---------|-----------------|
| **low** | Чтение, анализ | Просмотр кода, чтение памяти, генерация плана | Нет |
| **medium** | Изменение кода, staging | Создание ветки, изменение файлов, staging deploy | Для deploy |
| **high** | Инфраструктурные изменения | DB миграции, изменение env, restart сервисов | Да |
| **critical** | Production-влияющие действия | Production deploy, удаление данных, DNS, секреты | Да, обязательно |

## Модель разрешений (Permissions)

Каждый агент имеет JSONB-поле `permissions`:

```json
{
  "read_files": true,
  "write_files": true,
  "run_tests": true,
  "create_branch": true,
  "create_pr": true,
  "deploy_staging": true,
  "deploy_production": false,
  "change_env": false,
  "run_db_migrations": "approval_required",
  "restart_services": "approval_required",
  "delete_files": "approval_required",
  "access_secrets": false,
  "force_push": false,
  "delete_database": false
}
```

Значения:
- `true` — разрешено без approve
- `false` — запрещено
- `"approval_required"` — разрешено только через approve

## Approval Flow

### Когда нужен approve

1. **Code changes** (medium+ risk) — если задача меняет код
2. **Deploy to staging** — после выполнения и тестов
3. **Deploy to production** — всегда
4. **DB migrations** — всегда
5. **Env changes** — всегда
6. **Restart services** — всегда
7. **Delete files** — всегда

### MVP policy clarification

- **Staging deploy в MVP считается `approval_required`.**
- Любой deploy (staging/production) запускается только после явного approve в Telegram Approvals topic.

### Процесс approve

```
1. Агент завершает задачу → формирует plan/diff
2. Система создаёт Approval(status="pending")
3. Bot отправляет approval card в Telegram topic "Approvals"
4. Пользователь нажимает [Approve] или [Reject]
5. При approve → задача продолжает выполнение
6. При reject → задача отменяется
7. Все действия логируются в task_events
```

## Запрещённые действия

Агенты **никогда** не должны:

- Получать root shell без sandbox
- Читать приватные SSH-ключи
- Читать production `.env` в открытом виде
- Получать доступ к billing/API keys
- Удалять production database
- Выполнять `rm -rf` вне рабочей директории
- Делать force push
- Merge напрямую в `main` без approval
- Модифицировать `.ai_memory/README.md` без approve
- Изменять свои собственные permissions

## Sandbox изоляция

```yaml
# sandbox.compose.yml
services:
  agent-sandbox:
    image: amc-agent-sandbox:dev
    working_dir: /workspace
    volumes:
      - <restricted-workspace-mount>:/workspace:rw
    privileged: false
    cap_drop:
      - ALL
    read_only: true
    tmpfs:
      - /tmp:size=64m,mode=1777
    networks:
      - amc_sandbox_net
    mem_limit: 2g
    cpus: 2
    pids_limit: 256
    user: sandboxuser
    security_opt:
      - no-new-privileges:true
```

Дополнительно для DOP-02:
- По умолчанию **без** монтирования `/var/run/docker.sock`
- Sandbox network должен быть isolated/internal
- Production secrets не монтируются в sandbox
- Runtime `pip install` внутри sandbox запрещён (MVP)
- Зависимости для sandbox должны быть предустановлены в `Dockerfile.sandbox`

### WRK-04 DockerSandboxRunner (MVP ограничения)

- `FakeSandboxRunner` остаётся default.
- `DockerSandboxRunner` включается только opt-in флагом `SANDBOX_RUNNER_MODE=docker`.
- Mount policy: только validated task worktree → `/workspace` (без mount всего repo).
- В sandbox не передаются `.env`, secrets, `.ai_memory`, `docker.sock`.
- Network default для DockerSandboxRunner: `none` (без внешнего доступа).
- Для MVP поддерживается Linux worker host; Windows host path execution в DockerSandboxRunner не поддерживается.

### WRK-04-manual-test-hardening (May 2026)

- `DockerSandboxRunner.run()` принимает worktree prefix `manual-test-*` только при `SANDBOX_MANUAL_TEST_MODE=True`.
- В нормальном режиме (`SANDBOX_MANUAL_TEST_MODE=False`) разрешён только production-safe префикс `task-<external_id>-<short_uuid>`.
- `SANDBOX_MANUAL_TEST_MODE` **должен быть `False`** в production/staging; включается только временно и локально для manual smoke tests.
- Path traversal (выход за `.worktrees`) отклоняется всегда, независимо от режима.
- `build_worktree_path()` всегда генерирует только `task-*` префикс (production-safe).

## WRK-03 Command allowlist/denylist (hardened)

WRK-03-hardening реализован:

- **Allowlist** — только точные safe паттерны: `pytest`, `ruff check`, `compileall`, `git status/diff`, `pip list`
- **Denylist** — 55+ паттернов:
  - Shell escape: `sh -c`, `bash -c`, `python -c`, `powershell`, `pwsh`, `cmd /c`
  - Chaining operators: `&&`, `;`, `|`, `||`, backticks, `$()`
  - Network tools: `curl`, `wget`, `nc`, `netcat`, `telnet`, `ftp`, `scp`, `rsync`
  - Privilege escalation: `sudo`, `su`, `chmod`, `chown`
  - Git dangerous: `reset --hard`, `clean`, `clone`, `checkout`, `push/pull/fetch`, `merge`, `rebase`, `commit`
  - System/destructive: `docker`, `alembic`, `rm -rf`, `drop table`, `truncate`, `systemctl`, `deploy`
  - Secrets: `.env`, `token`, `password`
- **Denylist priority** — проверяется первым
- **Event type validation** — только 23 разрешённых event_type для `POST /events`
- Командное выполнение в sandbox разрешается только через future approval flow (WRK-03)

### WRK-04 Manual Docker sandbox test checklist

- Тестировать только локально (local host).
- `SANDBOX_RUNNER_MODE=docker` включать только временно на время теста.
- После manual test обязательно вернуть `SANDBOX_RUNNER_MODE=fake`.
- Не передавать `.env`/secrets в sandbox.
- Не подключаться к production/staging.
- Не выполнять deploy/migrations.
- Не монтировать repo root, `.ai_memory`, `docker.sock`.

## Audit Trail

Каждое действие логируется в таблицу `task_events`. Обязательные события:
- Все approve/reject решения
- Все deploy операции
- Все file changes
- Все command executions
- Все errors и failures
- Все permission changes

## Секреты

- `.env` файл на сервере (не в git)
- Docker secrets для production
- Агенты **не** имеют доступа к secrets напрямую
- Никогда не логировать значения secrets

## BE-04 Runtime Plan-Only Guardrails

- `RUNTIME_PROVIDER` поддерживает только `stub | opencode_http`, default=`stub`.
- Unknown provider обрабатывается fail-closed: `runtime_error` + `task_failed`, без fallback.
- `opencode_http` включается только через явный opt-in (`RUNTIME_PROVIDER=opencode_http`) и валидный `OPENCODE_SERVER_URL`; отсутствие обязательной конфигурации => fail-closed (`runtime_error` + `task_failed`).
- Production factory **не** создаёт fake transport для `opencode_http`; fake/mocked transport допускается только в тестах через explicit DI.
- Любая некорректная provider-конфигурация не должна иметь silent fallback на `stub`/`fake`.
- Plan-only policy: разрешены только действия `read/search/analyze/plan`; mutating/tooling/deploy/migrate/env-secrets операции блокируются через `policy_blocked`.
- Root confinement: canonical resolve + containment в `RUNTIME_ALLOWED_ROOT`; блокируются traversal, UNC/network paths, drive mismatch, absolute escape.
- Memory minimization: в runtime context передаются только `top-k` retrieval chunks (sanitized), full `.ai_memory` и `.env/secrets` не передаются.
- Redaction обязательна для runtime request payload, streamed deltas и payload task_events.
- SSE hardening (mock/fake in tests): timeout, malformed event handling, unknown event/tool handling, duplicate event dedupe, partial plan not final.
- Idempotency: `correlation_id`, `session_id`, `idempotency_key`, защита от дублирования финализации план-сессии.
- Approval invariants: `low=>approved`, `medium/high/critical=>waiting_approval + approval_requested`, adapter не может это обойти.
- Дополнительные event types: `runtime_session_created`, `runtime_event_received`, `policy_blocked`, `runtime_error`, `runtime_timeout`, `runtime_retry_scheduled`, `runtime_duplicate_event_ignored`, `runtime_event_malformed`.

## BE-11: Runtime Runbook Safety Rules

> **Reference:** Full runbook at `docs/runtime-runbook.md`. Scripts at `scripts/dev/`.

### Forbidden Operations (F1-F10)

The following operations are **hard-forbidden** in all BE-11 scripts and must never be performed during local runtime smoke testing:

| ID | Forbidden Operation | Enforcement |
|----|---------------------|-------------|
| F1 | `.env` file writes (create/edit/append) | Scripts never write to `.env` |
| F2 | Persistent environment changes (system/user-level) | `$env:VAR` process-scoped only; `Remove-Item Env:VAR` in `finally` |
| F3 | Production/staging server access | All URLs hardcoded to `127.0.0.1` |
| F4 | Deployment commands (docker compose up -d prod, systemctl, etc.) | No deploy commands in any script |
| F5 | Destructive database operations (DROP, TRUNCATE, DELETE) | `bootstrap-db.ps1` only runs `alembic upgrade head` |
| F6 | Binding to `0.0.0.0` | All listeners use `127.0.0.1` only |
| F7 | Port 3001 usage | Port 3001 excluded from all scripts |
| F8 | Mutating tool operations (write, execute, delete in sandbox) | Smoke tests only use plan-only flow |
| F9 | Credential or secret logging | `start-opencode.ps1` strips `OPENCODE_SERVER_PASSWORD`/`USERNAME` from child env |
| F10 | `DATABASE_URL` persistence | Set process-scoped in `bootstrap-db.ps1`, removed in `finally` |

### Abort Criteria (A1-A13)

Stop any smoke test immediately if:

| ID | Abort Condition | Detection |
|----|-----------------|-----------|
| A1 | Git working tree dirty | `git status --porcelain` check before and after |
| A2 | Service bound to `0.0.0.0` | `Get-NetTCPConnection` check for non-127.0.0.1 bindings |
| A3 | `/projects` returns 500 | API verification step |
| A4 | `.env` mutation detected | Git status shows `.env` changes |
| A5 | Stub fingerprints found in real OpenCode plan_text | 5 fingerprint patterns checked |
| A6 | Reasoning content leaked in plan_text | 3 reasoning patterns checked |
| A7 | `runtime_error` event emitted | Event analysis in smoke scripts |
| A8 | `runtime_timeout` event emitted | Event analysis in smoke scripts |
| A9 | `policy_blocked` event emitted | Event analysis in smoke scripts |
| A10 | `command_started` or `command_finished` event emitted | Sandbox execution check |
| A11 | `file_changed` or sandbox event emitted | File mutation check |
| A12 | Secret patterns in plan_text (`api_key=`, `token:`, `Bearer`, `sk-*`, `ghp_*`) | 4 regex patterns checked |
| A13 | Event ordering violation (`runtime_session_created` after `runtime_event_received`) | Index-based ordering check |

### Pre-Smoke Checklist (P1-P15)

Before running any smoke test, verify:

| ID | Check | Command/Script |
|----|-------|----------------|
| P1 | Docker daemon running | `docker info` |
| P2 | Compose file exists | `Test-Path infra/docker/docker-compose.yml` |
| P3 | Postgres container healthy | `.\scripts\dev\check-db.ps1` or `docker exec amc-dev-postgres pg_isready` |
| P4 | Redis container healthy | `docker exec amc-dev-redis redis-cli ping` → PONG |
| P5 | All 9 tables exist | `.\scripts\dev\check-db.ps1` (checks projects, agents, telegram_topics, tasks, task_events, approvals, memory_documents, memory_chunks, alembic_version) |
| P6 | Alembic version matches expected | `.\scripts\dev\check-db.ps1` (expected: `0001_initial_all_tables`) |
| P7 | Git working tree clean | `git status --porcelain` (must be empty) |
| P8 | No `.env` file modifications pending | Check `git diff .env` |
| P9 | `RUNTIME_PROVIDER=stub` (default) confirmed | Check API config or env |
| P10 | `RUNTIME_ALLOW_REAL_OPENCODE_HTTP=false` (default) confirmed | Check API config or env |
| P11 | `OPENCODE_SERVER_URL=""` (default) confirmed | Check API config or env |
| P12 | `SANDBOX_RUNNER_MODE=fake` (default) confirmed | Check worker config or env |
| P13 | No existing API on target port | `Get-NetTCPConnection -LocalPort 8000` |
| P14 | No existing OpenCode on target port | `Get-NetTCPConnection -LocalPort 4096` |
| P15 | `uvicorn`, `alembic`, `celery` available in Python environment | `python -c "import uvicorn; import alembic; import celery"` |

### Post-Smoke Checklist (T1-T12)

After running any smoke test, verify:

| ID | Check | Command/Script |
|----|-------|----------------|
| T1 | Git still clean (no file mutations) | `git status --porcelain` |
| T2 | No `.env` file changes | `git diff .env` |
| T3 | API returned to stub mode | `.\scripts\dev\cleanup-runtime.ps1 -DryRun` or `curl http://127.0.0.1:8000/health` |
| T4 | `RUNTIME_PROVIDER` env var removed | `$env:RUNTIME_PROVIDER` should be `$null` |
| T5 | `OPENCODE_SERVER_URL` env var removed | `$env:OPENCODE_SERVER_URL` should be `$null` |
| T6 | `RUNTIME_ALLOW_REAL_OPENCODE_HTTP` env var removed | `$env:RUNTIME_ALLOW_REAL_OPENCODE_HTTP` should be `$null` |
| T7 | `DATABASE_URL` env var not set process-scoped | `$env:DATABASE_URL` should be `$null` |
| T8 | OpenCode port (4096) free | `Get-NetTCPConnection -LocalPort 4096 -LocalAddress "127.0.0.1"` should be empty |
| T9 | Smok test artifacts cleaned | API test project/agent/task from timestamps `smoke-stub-*` / `smoke-real-*` |
| T10 | No orphaned processes on port 8000 | `Get-NetTCPConnection -LocalPort 8000` — only expected API |
| T11 | Postgres/Redis containers still running | `docker compose -f infra/docker/docker-compose.yml ps` |
| T12 | No secrets in smoke test output/logs | Manual review of console output |

### Secrets Handling (S1-S8)

| ID | Rule |
|----|------|
| S1 | Never write secrets to `.env` files |
| S2 | Never set secrets as persistent environment variables |
| S3 | `start-opencode.ps1` strips `OPENCODE_SERVER_PASSWORD` and `OPENCODE_SERVER_USERNAME` from child process env |
| S4 | `smoke-real-opencode-runtime.ps1` checks plan_text for 4 secret patterns: `api_key`/`token`/`secret`=`value`, `sk-*`, `ghp_*`, `Bearer` tokens |
| S5 | No credentials in script source code (verified by grep) |
| S6 | `bootstrap-db.ps1` sets `DATABASE_URL` process-scoped only; removes in `finally` |
| S7 | `DATABASE_URL` uses local dev credentials only (`agent_mc:agent_mc@localhost`) |
| S8 | All `Invoke-RestMethod` calls use `http://127.0.0.1` — no credentials in URLs |

### Worker Bypass Safety

Smoke test scripts (`smoke-stub-runtime.ps1`, `smoke-real-opencode-runtime.ps1`) use **direct `POST /runtime` API calls**, bypassing the Celery worker.

**Rationale:**
- Validates the API → OpenCode transport chain directly
- Celery worker is tested separately via `start-worker.ps1`
- Scripts print a prominent notice when bypassing

**Safety:** The API's own guardrails (idempotency, status gate, provider validation, plan-only policy) still apply. Worker bypass is for smoke convenience only.
