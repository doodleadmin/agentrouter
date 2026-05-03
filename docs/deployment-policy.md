# Политика деплоя — Agent Mission Control

Версия: 1.0
Дата: 2026-05-03

## Принципы

1. **Staging first** — сначала staging, потом production
2. **Tests required** — тесты должны пройти перед деплоем
3. **Approval for production** — production deploy только через approve
4. **Rollback ready** — всегда есть план отката
5. **Backup before migration** — бэкап БД перед миграциями

## Окружения

### Development (локальное)

- Цель: локальная разработка и тестирование
- Запуск: `docker compose up`
- БД: PostgreSQL в Docker
- Деплой: не требуется
- Docker images для сервисов готовятся через `infra/docker/Dockerfile.*`
- Sandbox config для WRK-03: `infra/docker/sandbox.compose.yml` (только `docker compose config` на текущем этапе)

### Staging

- Цель: тестирование перед production
- Branch: `develop` или feature branch
- Deploy: после явного approval
- БД: отдельная PostgreSQL на staging-сервере
- Требует approval: **да (MVP policy)**
- Smoke tests: да

### Production

- Цель: рабочее окружение
- Branch: `main` (только через PR)
- Deploy: **только через approval**
- БД: production PostgreSQL
- Требует approval: **да, обязательно**
- Backup: да, перед DB миграциями
- Smoke tests: да
- Rollback plan: обязателен

## Staging Deploy Flow

```
1. Агент завершает задачу
2. Тесты прошли
3. Агент запрашивает staging deploy
4. Approval card в Telegram (Approvals topic)
5. При approve запускается Deploy job:
   a. git clone + checkout branch
   b. docker compose build
   c. docker compose up -d
   d. smoke tests
6. Результат отправляется в Telegram
```

## Production Deploy Flow

```
1. PR merged в main
2. CI pipeline: tests → lint → build
3. Агент запрашивает production deploy
4. Approval card отправляется в Telegram:
   ┌────────────────────────────────────────┐
   │ 🚀 Production Deploy Request           │
   │                                        │
   │ Project: academy-bot                   │
   │ Branch: main                           │
   │ Commit: abc123                         │
   │ Risk: critical                         │
   │ Tests: ✅ passed                       │
   │ Migrations: 1 new (add_users_table)    │
   │ Env changes: none                      │
   │                                        │
   │ [✅ Approve]  [❌ Reject]  [📋 Diff]   │
   └────────────────────────────────────────┘
5. При approve:
   a. Backup БД (если есть миграции)
   b. docker compose -f docker-compose.prod.yml build
   c. docker compose -f docker-compose.prod.yml up -d
   d. smoke tests
   e. report в Telegram
```

## Rollback

### Production rollback

```bash
cd /opt/repos/<project>
git checkout <previous_tag>
docker compose -f docker-compose.prod.yml up -d --build

# Если была миграция — откатить:
alembic downgrade -1
```

## Запрещено

- Деплоить в production без approve
- Деплоить в production при упавших тестах
- Деплоить в production ветки, отличные от `main`
- Force push в `main`
- Изменять `.env.production` без approval

## DOP-02: Docker/Sandbox policy notes

- Dockerfiles (`Dockerfile.api`, `Dockerfile.telegram-bot`, `Dockerfile.worker`, `Dockerfile.sandbox`) — **dev/staging-ready only**.
- На этапе DOP-02 запрещены:
  - `docker build`
  - `docker compose up`
  - любой deploy
- В images запрещено хранить secrets и запрещено копировать `.env`.
- Sandbox execution будет включён только в WRK-03 approval flow.
- Runtime `pip install` внутри sandbox запрещён (MVP).
- Все зависимости для sandbox должны быть предустановлены в `infra/docker/Dockerfile.sandbox`.
- Внешний network для sandbox по умолчанию не используется (`network_mode=none`/internal-only policy).

### WRK-04 Manual Docker sandbox test (pre-deploy safety)

- Только local manual test, без staging/production окружений.
- `SANDBOX_RUNNER_MODE=docker` включается временно только на время проверки.
- После проверки режим обязан быть возвращён в `fake`.
- Запрещено выполнять deploy/migrations в рамках manual sandbox test.
- Запрещены mount repo root, `.ai_memory`, `docker.sock`, `.env`/secrets.
