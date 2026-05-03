# Agent Mission Control

Система управления AI-агентами через Telegram forum group, OpenCode и серверную инфраструктуру.

## Цель

Построить orchestration platform, где:

- **Telegram** — основной интерфейс управления (forum group с topics)
- **FastAPI** — control plane (REST API, роутинг, безопасность)
- **PostgreSQL** — state (проекты, агенты, задачи, approvals)
- **Redis** — очереди задач (Celery)
- **Obsidian vault** (`.ai_memory/`) — долгосрочная память проектов
- **pgvector** — семантический retrieval по памяти
- **OpenCode** — coding agent runtime
- **Docker** — sandbox для изолированного выполнения команд
- **Git worktree** — изолированные ветки на каждую задачу

## Архитектура

```
Telegram Forum Group
       ↓
Telegram Bot Gateway (aiogram)
       ↓
Orchestrator API (FastAPI)
       ↓
Task Queue (Celery + Redis)
       ↓
Agent Runtime Adapter (OpenCode)
       ↓
Docker Sandbox + Git Worktree
       ↓
Tests / PR / Deploy Pipeline
```

Полная архитектура: [docs/architecture.md](docs/architecture.md)

## Стек

| Компонент | Технология |
|-----------|-----------|
| Backend API | Python 3.12+, FastAPI, Pydantic v2 |
| Telegram Bot | aiogram 3.x |
| Database | PostgreSQL 16 + pgvector |
| Queue | Redis 7 + Celery |
| ORM | SQLAlchemy 2.x + Alembic |
| Agent Runtime | OpenCode server + SDK |
| Memory Vault | Obsidian-like vault в `.ai_memory/` + MCP |
| Sandbox | Docker Compose |
| Frontend | React + Vite + TailwindCSS + shadcn/ui (v2) |
| Reverse Proxy | Caddy или Nginx |

## Структура проекта

```
agentrouter/
├── .ai_memory/           ← ГЛАВНЫЙ Obsidian-like vault (source of truth)
│   ├── README.md         Правила vault
│   ├── _INDEX.md         Навигация
│   ├── current_state.md  Активный статус
│   ├── decisions/        ADR
│   ├── templates/        Шаблоны
│   ├── projects/         Профили проектов
│   ├── agents/           Профили агентов
│   └── tasks/            Логи задач
├── .opencode/            ← OpenCode runtime (агенты, конфиги)
├── docs/                 ← Проектная документация
│   ├── architecture.md
│   ├── roadmap.md
│   ├── mvp-backlog.md
│   └── ...
├── apps/                 ← Исходный код
│   ├── api/              FastAPI — Orchestrator API
│   ├── telegram-bot/     aiogram — Telegram Bot Gateway
│   ├── worker/           Celery — фоновые задачи
│   └── web/              React — Web Dashboard (v2)
├── infra/                ← Инфраструктура
│   ├── docker/           Docker Compose + Dockerfiles
│   └── deploy/           Деплой-конфигурации
├── README.md             ← Вы здесь
├── AGENTS.md             ← Правила для агентов
├── PROJECT_MEMORY.md     ← Краткий индекс → .ai_memory/
└── opencode.json         ← OpenCode конфигурация
```

## Roadmap

| Фаза | Цель | Статус |
|------|------|--------|
| Phase 0 | Подготовка инфраструктуры | Документация создана |
| Phase 1 | Telegram routing | Не начата |
| Phase 2 | Project memory + retrieval | Не начата |
| Phase 3 | OpenCode runtime (plan-only) | Не начата |
| Phase 4 | Safe code execution | Не начата |
| Phase 5 | PR workflow | Не начата |
| Phase 6 | Staging deploy | Не начата |
| Phase 7 | Production approval | Не начата |
| Phase 8 | Web dashboard | v2 |

Подробнее: [docs/roadmap.md](docs/roadmap.md), [docs/mvp-backlog.md](docs/mvp-backlog.md)

## Безопасность

- Production deploy только через approve
- DB миграции только через approve
- Агенты работают в Docker sandbox
- Нет прямого доступа к production secrets
- Все действия логируются в audit trail

Политика: [docs/security-policy.md](docs/security-policy.md)

## Память проекта

Главный vault: **`.ai_memory/`** (Obsidian-like, подключён к MCP через `opencode.json`).

Правила vault: [.ai_memory/README.md](.ai_memory/README.md)
Навигация: [.ai_memory/_INDEX.md](.ai_memory/_INDEX.md)
Текущий статус: [.ai_memory/current_state.md](.ai_memory/current_state.md)
Сводка: [PROJECT_MEMORY.md](PROJECT_MEMORY.md)

## Как начать

> Проект в стадии планирования. Код будет добавлен после утверждения архитектуры.

1. Скопировать `.env.example` в `.env` и заполнить переменные
2. Запустить `docker compose up` для поднятия PostgreSQL + Redis
3. Запустить API: `uvicorn apps.api.app.main:app --reload`
4. Настроить Telegram bot webhook

## Документация

- [Архитектура](docs/architecture.md)
- [MVP Backlog](docs/mvp-backlog.md)
- [Roadmap](docs/roadmap.md)
- [Схема БД](docs/database-schema.md)
- [Telegram flow](docs/telegram-flow.md)
- [Система памяти](docs/memory-system.md)
- [Политика безопасности](docs/security-policy.md)
- [Политика деплоя](docs/deployment-policy.md)
- [Роли агентов](docs/agent-roles.md)
