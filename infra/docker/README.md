# infra/docker — Docker Compose и Dockerfiles

## Назначение

Локальная инфраструктура и sandbox-конфиги для Agent Mission Control.

## Файлы

### `docker-compose.yml` (DOP-01, dev)
- PostgreSQL 16 + pgvector
- Redis 7
- API service для локальной разработки

### `Dockerfile.api` (DOP-02)
- Образ API сервиса (`apps/api`)
- Non-root user (`appuser`)
- Healthcheck: `GET /health`

### `Dockerfile.telegram-bot` (DOP-02)
- Образ Telegram Bot Gateway (`apps/telegram-bot`)
- Non-root user (`botuser`)
- Healthcheck: import check модуля

### `Dockerfile.worker` (DOP-02)
- Образ Celery worker (`apps/worker`)
- Non-root user (`workeruser`)
- Healthcheck: импорт `celery_app`

### `Dockerfile.sandbox` (DOP-02)
- Подготовленный runtime-образ для WRK-03 sandbox execution
- Non-root user (`sandboxuser`)
- Без secrets и без runtime task execution по умолчанию

### `sandbox.compose.yml` (DOP-02)
Изолированный sandbox-compose для будущего WRK-03:
- `no-new-privileges:true`
- `cap_drop: [ALL]`
- `privileged: false`
- `read_only: true` + `tmpfs` для `/tmp`
- CPU/RAM/PID limits (`cpus: 2.0`, `mem_limit: 2g`, `pids_limit: 256`)
- isolated internal network (`amc_sandbox_net`)
- без `docker.sock`

## Политика безопасности Docker

- Не копировать `.env` в image layers.
- Не хранить secrets/tokens/passwords в Dockerfile.
- Не использовать privileged containers.
- Сетевой доступ sandbox — только через отдельную internal сеть.

## Проверка конфигурации (без запуска)

```bash
docker compose -f infra/docker/sandbox.compose.yml config
```

## Статус

- DOP-01: ✅ выполнен
- DOP-02: ✅ Dockerfiles + sandbox compose подготовлены
