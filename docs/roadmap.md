# Roadmap — Agent Mission Control

Версия: 1.0
Дата: 2026-05-03

## Обзор

Разработка ведётся по 8 фазам, от инфраструктуры до web dashboard. Каждая фаза — это один спринт (1-2 недели).

```
Phase 0: Инфраструктура    ████████░░░░░░░░░░░░  Документация готова
Phase 1: Telegram routing   ░░░░░░░░████████░░░░  Не начата
Phase 2: Project memory     ░░░░░░░░░░░░████░░░░  Не начата
Phase 3: OpenCode runtime   ░░░░░░░░░░░░░░░░████  Не начата
Phase 4: Safe execution     ░░░░░░░░░░░░░░░░░░░░  Не начата
Phase 5: PR workflow        ░░░░░░░░░░░░░░░░░░░░  Не начата
Phase 6: Staging deploy     ░░░░░░░░░░░░░░░░░░░░  Не начата
Phase 7: Production deploy  ░░░░░░░░░░░░░░░░░░░░  Не начата
Phase 8: Web dashboard      ░░░░░░░░░░░░░░░░░░░░  Не начата
```

---

## Phase 0: Подготовка инфраструктуры

**Цель:** Сервер готов, репозиторий создан, базовые сервисы запускаются.
**Спринт:** 1 неделя
**Ответственные:** devops-automator, backend-architect

### Задачи

| # | Задача | Агент | Приоритет |
|---|--------|-------|-----------|
| 0.1 | Создать monorepo, инициализировать git | git-workflow-master | high |
| 0.2 | `docker-compose.yml`: PostgreSQL 16 + pgvector, Redis 7 | devops-automator | high |
| 0.3 | FastAPI каркас: `main.py`, `config.py`, lifespan, CORS | backend-architect | high |
| 0.4 | SQLAlchemy модели: все 8 таблиц | backend-architect | high |
| 0.5 | Alembic: init + первая миграция | backend-architect | high |
| 0.6 | `.env.example` с переменными | devops-automator | medium |
| 0.7 | `AGENTS.md` для проекта | knowledge-steward | medium |
| 0.8 | Структура `.ai_memory/` vault | knowledge-steward | medium |

### Результат
- `docker compose up` поднимает PostgreSQL + Redis
- `uvicorn` запускает FastAPI с healthcheck `/health`
- Миграции накатываются через `alembic upgrade head`

---

## Phase 1: Telegram Routing

**Цель:** Сообщения из топиков группы превращаются в задачи.
**Спринт:** 1-2 недели
**Ответственные:** backend-architect, devops-automator
**Зависимость:** Phase 0

### Задачи

| # | Задача | Агент | Риск |
|---|--------|-------|------|
| 1.1 | Создать Telegram bot через BotFather | devops-automator | low |
| 1.2 | Создать Telegram supergroup с topics | devops-automator | low |
| 1.3 | aiogram webhook handler | backend-architect | low |
| 1.4 | Сохранять `chat_id` + `message_thread_id` | backend-architect | low |
| 1.5 | CRUD endpoints: `/projects`, `/agents` | backend-architect | low |
| 1.6 | Команда `/bind_topic agent backend` | backend-architect | low |
| 1.7 | Routing service: topic → kind → task creation | backend-architect | medium |
| 1.8 | Ответ бота в тот же topic | backend-architect | low |
| 1.9 | Команды `/projects`, `/agents`, `/tasks` | backend-architect | low |
| 1.10 | Intent classifier (базовый) | backend-architect | medium |

### Результат
- Сообщение в topic создаёт Task в БД
- Bot отвечает в тот же topic
- `/bind_topic` привязывает topic к агенту или проекту

---

## Phase 2: Project Memory

**Цель:** У каждого проекта есть markdown-память с семантическим retrieval.
**Спринт:** 1-2 недели
**Ответственные:** backend-architect, knowledge-steward
**Зависимость:** Phase 1

### Задачи

| # | Задача | Агент | Риск |
|---|--------|-------|------|
| 2.1 | Шаблоны memory-файлов при создании проекта | knowledge-steward | low |
| 2.2 | CRUD для memory files (read/write/append) | backend-architect | medium |
| 2.3 | Markdown indexer: read → parse → chunk | backend-architect | medium |
| 2.4 | pgvector extension + embedding pipeline | backend-architect | medium |
| 2.5 | `POST /memory/search` endpoint | backend-architect | medium |
| 2.6 | Auto-index при изменении memory-файлов | backend-architect | medium |
| 2.7 | `/memory search project=X query=...` в Telegram | backend-architect | low |
| 2.8 | Summary writer: после задач → agent-notes.md | knowledge-steward | low |

### Результат
- При добавлении проекта создаётся vault с шаблонами
- Memory индексируется и доступна через `/memory/search`
- Агенты могут искать релевантный контекст

---

## Phase 3: OpenCode Runtime (Plan-Only)

**Цель:** Агент получает задачу + память и возвращает план.
**Спринт:** 1-2 недели
**Ответственные:** backend-architect, devops-automator
**Зависимость:** Phase 2

### Задачи

| # | Задача | Агент | Риск |
|---|--------|-------|------|
| 3.1 | Поднять OpenCode server | devops-automator | medium |
| 3.2 | Реализовать `AgentRuntimeAdapter` interface | backend-architect | medium |
| 3.3 | OpenCode adapter implementation | backend-architect | medium |
| 3.4 | Prompt builder: task + memory + AGENTS.md + rules | backend-architect | medium |
| 3.5 | Plan-only execution (читает, возвращает план) | backend-architect | medium |
| 3.6 | Отправка плана в Telegram | backend-architect | low |
| 3.7 | Approval request для medium+ задач | backend-architect | medium |

### Результат
- Агент отвечает планом на основе памяти проекта
- План отправляется в Telegram topic
- Medium/high задачи требуют approve перед выполнением

---

## Phase 4: Safe Code Execution

**Цель:** Агент может менять код в изолированной ветке после approve.
**Спринт:** 2 недели
**Ответственные:** backend-architect, devops-automator, git-workflow-master
**Зависимость:** Phase 3

### Задачи

| # | Задача | Агент | Риск |
|---|--------|-------|------|
| 4.1 | Git worktree per task | git-workflow-master | medium |
| 4.2 | Docker sandbox compose | devops-automator | high |
| 4.3 | Approved execution flow | backend-architect | high |
| 4.4 | Run tests в sandbox | backend-architect | medium |
| 4.5 | Diff summary | git-workflow-master | medium |
| 4.6 | Commit changes | git-workflow-master | medium |
| 4.7 | Write run summary в memory | knowledge-steward | low |

### Результат
- Агент выполняет код в Docker sandbox
- Изменения в отдельном git worktree
- Tests запускаются автоматически
- Diff summary отправляется в Telegram

---

## Phase 5: PR Workflow

**Цель:** Агент создаёт PR/MR.
**Спринт:** 1 неделя
**Ответственные:** backend-architect, git-workflow-master
**Зависимость:** Phase 4

### Задачи

| # | Задача | Агент | Риск |
|---|--------|-------|------|
| 5.1 | GitHub/GitLab API integration | backend-architect | medium |
| 5.2 | Push branch → create PR | git-workflow-master | medium |
| 5.3 | Attach summary to PR description | backend-architect | low |
| 5.4 | Save PR link в task record | backend-architect | low |

### Результат
- Агент создаёт PR с описанием изменений
- PR link сохраняется в задаче

---

## Phase 6: Staging Deploy

**Цель:** Агент может деплоить staging после прохождения тестов.
**Спринт:** 1 неделя
**Ответственные:** backend-architect, devops-automator, reality-checker
**Зависимость:** Phase 5

### Задачи

| # | Задача | Агент | Риск |
|---|--------|-------|------|
| 6.1 | Deploy commands в memory/project/deployment.md | knowledge-steward | low |
| 6.2 | Deploy Celery job | backend-architect | high |
| 6.3 | Smoke tests после деплоя | reality-checker | medium |
| 6.4 | Deploy report в Telegram | backend-architect | medium |

### Результат
- Staging deploy автоматический после approve
- Smoke tests проверяют базовую работоспособность
- Результат отправляется в Telegram

---

## Phase 7: Production Approval

**Цель:** Production deploy только через explicit approve.
**Спринт:** 1 неделя
**Ответственные:** backend-architect, devops-automator, security-engineer
**Зависимость:** Phase 6

### Задачи

| # | Задача | Агент | Риск |
|---|--------|-------|------|
| 7.1 | Approval cards в Telegram (Approve/Reject) | backend-architect | medium |
| 7.2 | Audit log viewer API | backend-architect | medium |
| 7.3 | Production deploy job с backup | devops-automator | critical |
| 7.4 | Rollback command | devops-automator | critical |
| 7.5 | Deploy report | backend-architect | low |
| 7.6 | Security review production flow | security-engineer | high |

### Результат
- Production deploy требует approve через Telegram
- Audit trail для всех действий
- Rollback доступен в один клик

---

## Phase 8: Web Dashboard

**Цель:** Web UI в стиле Mission Control.
**Спринт:** 2-3 недели
**Ответственные:** frontend-developer, backend-architect
**Зависимость:** Phase 7

### Задачи

| # | Задача | Агент | Риск |
|---|--------|-------|------|
| 8.1 | React + Vite + TailwindCSS + shadcn/ui setup | frontend-developer | low |
| 8.2 | Agents list page | frontend-developer | low |
| 8.3 | Task queue с SSE/WebSocket live updates | frontend-developer | medium |
| 8.4 | Project cards page | frontend-developer | low |
| 8.5 | Memory file viewer | frontend-developer | medium |
| 8.6 | Approval management page | frontend-developer | medium |
| 8.7 | System status / health | frontend-developer | low |
| 8.8 | SSE endpoint в FastAPI | backend-architect | medium |

### Результат
- Полноценный web dashboard
- Live updates через SSE/WebSocket
- Все операции доступны через UI

---

## Критерии завершения MVP

MVP считается готовым после Phase 7:

- [ ] Telegram bot принимает сообщения из forum topics
- [ ] Topic корректно маппится на агента или проект
- [ ] Можно зарегистрировать проект
- [ ] Для проекта создаётся markdown memory vault
- [ ] Memory индексируется и доступна через search
- [ ] Агент получает задачу и возвращает plan
- [ ] Агент выполняет approved-задачу в git worktree
- [ ] Команды запускаются в sandbox
- [ ] Bot возвращает diff summary и test results
- [ ] Результат задачи записывается в memory
- [ ] Production deploy невозможен без approval
