# infra — Инфраструктура

## Описание

Инфраструктурные конфигурации для локальной разработки и подготовки безопасного sandbox execution.

## Структура

```text
infra/
├── docker/
│   ├── docker-compose.yml          # DOP-01: dev postgres/redis/api
│   ├── Dockerfile.api              # DOP-02
│   ├── Dockerfile.telegram-bot     # DOP-02
│   ├── Dockerfile.worker           # DOP-02
│   ├── Dockerfile.sandbox          # DOP-02
│   ├── sandbox.compose.yml         # DOP-02 (future WRK-03 sandbox)
│   └── README.md
├── deploy/                         # future staging/prod deployment configs
└── README.md
```

## Безопасность

- Sandbox контейнеры: non-root, no-new-privileges, no privileged mode.
- Нет подключения `docker.sock` по умолчанию.
- Нет монтирования production secrets.
- Resource limits обязательны для sandbox.

## Статус

- DOP-01: ✅ dev docker-compose
- DOP-02: ✅ Dockerfiles + sandbox compose
