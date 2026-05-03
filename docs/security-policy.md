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
