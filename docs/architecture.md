# Архитектура системы Agent Mission Control

Версия: 1.0
Дата: 2026-05-03

## Обзор

Agent Mission Control — это orchestration platform для управления AI-агентами. Система состоит из трёх основных слоёв:

1. **Telegram UI** — пользователь управляет агентами через forum group
2. **Orchestrator API** — контрольный слой: роутинг, память, безопасность, задачи
3. **Agent Runtime** — выполнение задач через OpenCode в изолированном sandbox

## Диаграмма

```
┌──────────────────────────────────────────────────────────┐
│                  Telegram Forum Group                     │
│  General | Agent:Backend | Agent:Frontend | Approvals    │
└──────────────────────┬───────────────────────────────────┘
                       │ Bot API (webhook / long polling)
┌──────────────────────▼───────────────────────────────────┐
│             Telegram Bot Gateway (aiogram 3.x)           │
│  Приём сообщений → парсинг команд → ответ в topic        │
└──────────────────────┬───────────────────────────────────┘
                       │ HTTP API
┌──────────────────────▼───────────────────────────────────┐
│              Orchestrator API (FastAPI)                   │
│                                                          │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │  Routing    │  │  Memory     │  │  Security        │  │
│  │  Service    │  │  Service    │  │  Service         │  │
│  │            │  │  (vault +   │  │  (permissions +  │  │
│  │  intent →  │  │   pgvector) │  │   risk + audit)  │  │
│  │  agent →   │  │             │  │                  │  │
│  │  project   │  │             │  │                  │  │
│  └────────────┘  └─────────────┘  └──────────────────┘  │
│                                                          │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │  Task      │  │  Approval   │  │  Runtime         │  │
│  │  Service   │  │  Service    │  │  Adapter         │  │
│  │            │  │             │  │  (OpenCode SDK)  │  │
│  └────────────┘  └─────────────┘  └──────────────────┘  │
└───────┬──────────────┬──────────────┬───────────────────┘
        │              │              │
   ┌────▼────┐   ┌─────▼─────┐  ┌────▼────────────┐
   │PostgreSQL│   │   Redis   │  │ Markdown Vault  │
   │+pgvector │   │ + Celery  │  │ (.ai_memory/)   │
   │          │   │           │  │                  │
   │projects  │   │ queues:   │  │ global/          │
   │agents    │   │ inbound   │  │ projects/        │
   │tasks     │   │ plan      │  │ agents/          │
   │approvals │   │ execute   │  │ decisions/       │
   │events    │   │ deploy    │  │ tasks/           │
   │memory    │   │ index     │  │                  │
   └──────────┘   └───────────┘  └─────────────────┘
                                        │
                               ┌────────▼─────────┐
                               │  Agent Runtime   │
                               │  (OpenCode)      │
                               │                  │
                               │  git worktree    │
                               │  Docker sandbox  │
                               │  tests / lint    │
                               └──────────────────┘
```

## Сервисы

### 1. Orchestrator API (FastAPI)

**Порт:** 8000
**Роль:** Центральный контрольный слой

Ответственности:
- REST API для всех операций
- Роутинг сообщений: intent → agent → project → risk
- CRUD для проектов, агентов, задач
- Memory retrieval (search)
- Approval management
- Audit logging

Endpoints:
```
POST   /telegram/webhook          — приём Telegram updates
GET    /health                    — healthcheck

GET    /projects                  — список проектов
POST   /projects                  — создать проект
GET    /projects/{slug}           — получить проект
PATCH  /projects/{slug}           — обновить проект

GET    /agents                    — список агентов
POST   /agents                    — создать агента
GET    /agents/{slug}             — получить агента
PATCH  /agents/{slug}             — обновить агента

POST   /tasks                     — создать задачу
GET    /tasks/{id}                — получить задачу
POST   /tasks/{id}/approve        — одобрить задачу
POST   /tasks/{id}/reject         — отклонить задачу
POST   /tasks/{id}/cancel         — отменить задачу

POST   /memory/search             — семантический поиск
GET    /memory/file?path=...      — прочитать файл памяти
POST   /memory/reindex            — переиндексация

POST   /runtime/sessions          — создать сессию агента
GET    /runtime/sessions/{id}/events — стрим событий
POST   /runtime/sessions/{id}/stop   — остановить сессию
```

### 2. Telegram Bot Gateway (aiogram)

**Роль:** Интерфейс между Telegram и API

Ответственности:
- Приём сообщений из forum topics
- Парсинг команд (`/bind_topic`, `/projects`, `/agents`, `/task`, `/plan`, `/run`, `/memory`, `/deploy`)
- Маршрутизация: topic → kind (agent/project/general) → task creation
- Форматирование ответов (markdown, inline-кнопки для approvals)
- Отправка ответов в тот же topic

### 3. Celery Worker

**Роль:** Фоновое выполнение задач

Очереди:
- `telegram_inbound` — обработка входящих сообщений
- `agent_plan` — генерация плана агентом
- `agent_execute` — выполнение задачи агентом
- `memory_index` — индексация памяти
- `deploy_staging` — staging deploy
- `deploy_production` — production deploy (требует approval)
- `notifications` — отправка уведомлений

### 4. React Dashboard (v2)

**Порт:** 3000
**Роль:** Web UI

Страницы:
- Dashboard — обзор системы
- Agents — список агентов и статусы
- Tasks — очередь задач
- Projects — карточки проектов
- Memory — просмотр vault
- Approvals — управление подтверждениями

## Поток данных: типичная задача

```
1. Пользователь пишет в Telegram topic:
   "@bot project=my-app добавь healthcheck endpoint"

2. Bot Gateway получает сообщение:
   - chat_id, message_thread_id, text, user_id

3. API routing_service:
   - определяет topic → agent или project
   - классифицирует intent → "code_change"
   - определяет risk_level → "medium"
   - создаёт Task(status="created")

4. Memory service:
   - retrieves memory по project "my-app"
   - возвращает: stack.md, architecture.md, commands.md

5. Celery worker (agent_plan):
   - создаёт OpenCode сессию
   - передаёт: task + memory + AGENTS.md + rules
   - получает plan

6. API отправляет plan в Telegram:
   - "Plan: 1) ..., 2) ... / Requires approval: yes"
   - inline-кнопки: [Approve] [Reject]

7. Пользователь нажимает [Approve]:
   - API создаёт Approval(status="approved")
   - Celery worker (agent_execute):
     - создаёт git worktree
     - запускает Docker sandbox
     - агент выполняет изменения
     - запускает tests
     - собирает diff

8. API отправляет результат:
   - summary + changed files + test results
   - "PR created: https://github.com/..."

9. Memory service:
   - записывает run summary в .ai_memory/tasks/
   - обновляет agent-notes.md
   - переиндексирует память
```

## Изоляция и безопасность

### Docker Sandbox
- Каждая задача выполняется в отдельном Docker контейнере
- Контейнер монтирует только нужный git worktree
- Ограничения: mem_limit=2g, cpus=2
- Нет доступа к сети, кроме нужных сервисов
- Нет доступа к secrets

### Git Worktree
- Каждая задача получает отдельный worktree
- Ветка: `agent/<task-id>`
- Нет доступа к другим worktree
- После завершения — cleanup

### Permissions
- Агенты имеют гранулярные разрешения (JSONB в agents.permissions)
- Risk level определяет, нужно ли approval
- Audit trail для каждого действия

## Масштабирование

### Горизонтальное
- Несколько Celery workers для параллельных задач
- API stateless — можно запускать несколько инстансов
- PostgreSQL read replicas при росте нагрузки

### Вертикальное
- pgvector → Qdrant при росте векторного индекса
- Redis cluster при росте очередей
- S3 / MinIO для хранения артефактов

## Границы сервисов (Module Boundaries)

```
apps/api/app/
├── routers/        → HTTP endpoints (thin controllers)
├── services/       → Business logic (one service per domain)
├── models/         → SQLAlchemy models
├── db/             → Database setup, sessions, migrations
├── workers/        → Celery tasks
├── integrations/   → External APIs (telegram, opencode, github)
├── memory/         → Indexing, chunking, embedding, retrieval
└── security/       → Permissions, risk, audit
```

Правила:
- Routers вызывают только Services
- Services вызывают Models, Integrations, Memory
- Workers вызывают Services
- Интеграции не знают друг о друге
- Memory module самодостаточен
