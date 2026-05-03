# Task Summary: DOP-02 — Dockerfiles + sandbox compose

**Дата:** 2026-05-03  
**Агент:** devops-automator  
**Статус:** ✅ Выполнена

---

## Цель

Подготовить Dockerfiles и sandbox compose для безопасного будущего выполнения задач в WRK-03 без запуска контейнеров и без деплоя.

## Что сделано

### Dockerfiles

- `infra/docker/Dockerfile.api`
  - Python 3.12 slim
  - non-root user `appuser`
  - install из `apps/api`
  - healthcheck: HTTP `GET /health`

- `infra/docker/Dockerfile.telegram-bot`
  - Python 3.12 slim
  - non-root user `botuser`
  - install из `apps/telegram-bot`
  - healthcheck: import check

- `infra/docker/Dockerfile.worker`
  - Python 3.12 slim
  - non-root user `workeruser`
  - install из `apps/worker`
  - healthcheck: `celery_app` import check

- `infra/docker/Dockerfile.sandbox`
  - Python 3.12 slim
  - non-root user `sandboxuser`
  - workdir `/workspace`
  - минимальный runtime (bash/git/curl)
  - placeholder command (без реального task execution)

### Sandbox compose

- `infra/docker/sandbox.compose.yml`
  - `privileged: false`
  - `security_opt: [no-new-privileges:true]`
  - `cap_drop: [ALL]`
  - `read_only: true` + `tmpfs /tmp`
  - `mem_limit: 2g`, `cpus: 2.0`, `pids_limit: 256`
  - isolated internal network `amc_sandbox_net`
  - no docker.sock mounts
  - bounded bind mount for workspace (`/workspace`)

### Документация

- `infra/docker/README.md`
- `infra/README.md`
- `docs/deployment-policy.md`
- `docs/security-policy.md`

Документация синхронизирована с DOP-02 и описывает ограничения sandbox и запреты на build/up/deploy на текущем этапе.

## Проверка

Разрешённая проверка выполнена:

```bash
docker compose -f infra/docker/sandbox.compose.yml config
```

Результат: ✅ конфигурация валидна.

## Ограничения соблюдены

- Не запускались `docker build`
- Не запускались `docker compose up`
- Не выполнялся deploy
- Не менялись `.env`/secrets
- Не было подключений к production/staging

## Следующие шаги

1. WRK-03: использовать `sandbox.compose.yml` в approval-driven execute pipeline.
2. Подключить task-specific worktree mount вместо общего bind для production-safe flow.
