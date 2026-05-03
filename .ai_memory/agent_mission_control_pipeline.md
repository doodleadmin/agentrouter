# Agent Mission Control: пайплайн реализации мультиагентной системы через Telegram + OpenCode

Версия: 1.0  
Цель документа: дать агентам полный маршрут реализации проекта: архитектура, инструменты, память по проектам, Telegram-форум, OpenCode runtime, безопасный деплой, этапы MVP и правила работы.

---

## 1. Что строим

Нужно реализовать систему управления AI-агентами, где:

- основной интерфейс управления — Telegram-группа с включенными Topics / Forum;
- каждый Telegram-топик соответствует отдельному агенту или рабочему направлению;
- `General` используется для общего чата, статусов, координации и системных уведомлений;
- агенты знают список проектов пользователя и контекст каждого проекта;
- проекты лежат на сервере в виде git-репозиториев;
- агенты могут анализировать код, писать изменения, запускать тесты, создавать PR, готовить деплой;
- опасные действия выполняются только после подтверждения пользователя;
- память по проектам устроена как Obsidian-like vault: markdown-файлы + связи + индекс + retrieval;
- в будущем можно добавить web UI в стиле Mission Control.

---

## 2. Главный принцип архитектуры

OpenCode не должен быть всей системой целиком. Его роль — coding agent runtime.

Telegram bot, память, права доступа, проекты, очереди задач, деплой и audit log должны быть реализованы в отдельном orchestration layer.

```text
Telegram Forum Group
        ↓
Telegram Bot Gateway
        ↓
Orchestrator API
        ↓
Task Queue
        ↓
Agent Runtime Adapter
        ↓
OpenCode Server / SDK
        ↓
Project Workspace / Git Worktree / Docker Sandbox
        ↓
Tests / PR / Deploy Pipeline
```

---

## 3. Рекомендуемый стек

### 3.1 Backend

Основной вариант:

- Python 3.12+
- FastAPI
- aiogram 3.x для Telegram Bot API
- PostgreSQL
- pgvector для retrieval memory
- Redis
- Celery или Dramatiq для фоновых задач
- SQLAlchemy 2.x или SQLModel
- Alembic для миграций
- Pydantic v2

Альтернативный вариант:

- Node.js / TypeScript
- NestJS или Hono
- Telegraf
- PostgreSQL
- Redis + BullMQ
- OpenCode JS/TS SDK

Так как основной разработчик работает с Python и React, базовый вариант — Python backend + React dashboard.

### 3.2 Agent runtime

- OpenCode server
- OpenCode SDK или HTTP API
- AGENTS.md в каждом проекте
- отдельные agent profiles: backend, frontend, devops, researcher, qa, pm

### 3.3 Память

- Markdown vault на сервере
- PostgreSQL для структурных данных
- pgvector или Qdrant для векторного поиска
- локальный file indexer
- optional: MCP-compatible слой для доступа к markdown vault

### 3.4 Деплой

- Docker
- Docker Compose
- GitHub Actions или GitLab CI
- staging-first workflow
- production deploy только после approve
- Caddy или Nginx
- systemd для сервисов, если нужно
- Sentry / Grafana / Prometheus позже

### 3.5 Frontend позже

- React
- Vite или Next.js
- TailwindCSS
- shadcn/ui
- WebSocket / SSE для live task updates

---

## 4. Telegram как интерфейс управления

### 4.1 Структура группы

Создать Telegram supergroup с включенным режимом Topics / Forum.

Рекомендуемые топики:

```text
General
Agent: Backend
Agent: Frontend
Agent: DevOps
Agent: Research
Agent: QA
Agent: PM
Project: project-a
Project: project-b
System Logs
Approvals
```

Есть два возможных подхода.

### Подход A: топик = агент

```text
Agent: Backend → backend_agent
Agent: Frontend → frontend_agent
Agent: DevOps → devops_agent
```

Плюсы:

- просто маршрутизировать задачи;
- удобно общаться с конкретным агентом;
- агент имеет постоянный чат-контекст.

Минусы:

- если проектов много, нужно явно указывать проект в сообщении.

Пример:

```text
@bot project=academy-bot добавь healthcheck endpoint и тесты
```

### Подход B: топик = проект

```text
Project: academy-bot
Project: fashion-crm
Project: wellness-platform
```

Плюсы:

- весь контекст проекта в одном топике;
- удобно вести историю по проекту.

Минусы:

- нужно явно указывать агента или orchestrator должен сам выбирать роль.

Пример:

```text
@backend добавь healthcheck endpoint и тесты
```

### Рекомендация

Для MVP использовать гибрид:

```text
General → общий роутер
Agent:* → персональные топики агентов
Project:* → проектные топики для крупных проектов
Approvals → подтверждения опасных действий
System Logs → логи задач, ошибок, деплоев
```

---

## 5. Роутинг сообщений из Telegram

Каждое входящее сообщение содержит:

- `chat_id`
- `message_thread_id`
- `user_id`
- `text`
- `reply_to_message`, если есть
- attachments, если есть

Логика:

```python
async def route_telegram_message(message):
    chat_id = message.chat.id
    thread_id = message.message_thread_id
    text = message.text or ""

    topic = await db.topics.get_by_chat_and_thread(chat_id, thread_id)

    if topic.kind == "agent":
        agent = await db.agents.get(topic.agent_id)
        project = await detect_project(text, topic)
        return await create_agent_task(agent, project, text)

    if topic.kind == "project":
        project = await db.projects.get(topic.project_id)
        agent = await detect_agent(text, project)
        return await create_agent_task(agent, project, text)

    if topic.kind == "general":
        intent = await classify_intent(text)
        return await orchestrator_handle(intent, text)
```

---

## 6. Память по проектам как Obsidian-like vault

### 6.1 Цель памяти

Память нужна, чтобы агенты знали:

- какие проекты существуют;
- где лежат репозитории;
- какой стек у каждого проекта;
- как запускать проект;
- как тестировать;
- как деплоить;
- какие правила разработки;
- какие текущие задачи;
- какие решения уже были приняты;
- какие ошибки и инциденты были раньше;
- какие домены, сервисы и окружения связаны с проектом.

### 6.2 Структура vault

```text
/opt/agent-control/memory
  /global
    index.md
    user-profile.md
    agents.md
    infrastructure.md
    deployment-rules.md
    security-rules.md
    glossary.md

  /projects
    /academy-bot
      project.md
      stack.md
      architecture.md
      commands.md
      deployment.md
      environment.md
      decisions.md
      tasks.md
      incidents.md
      changelog.md
      links.md
      agent-notes.md

    /fashion-crm
      project.md
      stack.md
      architecture.md
      commands.md
      deployment.md
      environment.md
      decisions.md
      tasks.md
      incidents.md
      changelog.md
      links.md
      agent-notes.md

  /agents
    backend-agent.md
    frontend-agent.md
    devops-agent.md
    researcher-agent.md
    qa-agent.md
    pm-agent.md

  /runs
    /2026-01-15-task-0001.md
    /2026-01-15-task-0002.md
```

### 6.3 Главный файл проекта: `project.md`

Шаблон:

```markdown
# Project: academy-bot

## Summary
Краткое описание проекта.

## Owner
Слава

## Repository
/opt/agent-control/repos/academy-bot

## Production
- domain:
- server:
- deploy method:

## Staging
- domain:
- server:
- deploy method:

## Stack
- Python:
- Framework:
- Database:
- Queue:
- Frontend:

## Important Commands
См. commands.md

## Deployment
См. deployment.md

## Current Priorities
- ...

## Known Risks
- ...

## Agent Rules
- Перед изменениями создать отдельную ветку.
- Перед деплоем запускать тесты.
- Production deploy только после approve.
```

### 6.4 `commands.md`

```markdown
# Commands

## Install
```bash
poetry install
```

## Run dev
```bash
poetry run uvicorn app.main:app --reload
```

## Test
```bash
pytest
```

## Lint
```bash
ruff check .
```

## Typecheck
```bash
mypy .
```

## Build docker
```bash
docker compose build
```
```

### 6.5 `deployment.md`

```markdown
# Deployment

## Environments

### Staging
- branch: develop
- deploy command: docker compose -f docker-compose.staging.yml up -d --build
- requires approval: no

### Production
- branch: main
- deploy command: docker compose -f docker-compose.prod.yml up -d --build
- requires approval: yes

## Pre-deploy checklist
- tests passed
- migrations reviewed
- env changes reviewed
- backup created if DB migration exists

## Rollback
```bash
git checkout <previous_tag>
docker compose -f docker-compose.prod.yml up -d --build
```
```

### 6.6 `decisions.md`

Файл для архитектурных решений.

```markdown
# Decisions

## ADR-0001: Use FastAPI for backend

Date: 2026-01-15
Status: accepted

## Context
...

## Decision
...

## Consequences
...
```

### 6.7 `agent-notes.md`

Файл, куда агенты пишут краткие выводы после задач.

```markdown
# Agent Notes

## 2026-01-15 / backend-agent / task-0001

Изменения:
- добавлен healthcheck endpoint
- добавлен тест

Важно для будущих задач:
- auth middleware не применяется к /health
- тесты запускаются через pytest
```

---

## 7. Индексация памяти

### 7.1 Что индексируем

- `/memory/global/**/*.md`
- `/memory/projects/**/*.md`
- `README.md` в репозиториях
- `AGENTS.md` в репозиториях
- `docs/**/*.md` в репозиториях
- последние task summaries
- deployment logs
- incidents

### 7.2 Как индексируем

Pipeline:

```text
File changed
    ↓
Markdown parser
    ↓
Chunker
    ↓
Embedding model
    ↓
pgvector / Qdrant
    ↓
Retrieval API
```

### 7.3 Таблица для индекса

```sql
CREATE TABLE memory_documents (
    id UUID PRIMARY KEY,
    scope TEXT NOT NULL,
    project_id UUID NULL,
    path TEXT NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE memory_chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES memory_documents(id) ON DELETE CASCADE,
    project_id UUID NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Размерность `VECTOR(1536)` зависит от выбранной embedding-модели. Если модель другая, размерность нужно заменить.

### 7.4 Retrieval API

```http
POST /memory/search
```

Body:

```json
{
  "query": "как деплоить academy-bot на staging",
  "project_id": "academy-bot",
  "scope": ["project", "global"],
  "limit": 8
}
```

Ответ:

```json
{
  "items": [
    {
      "path": "/memory/projects/academy-bot/deployment.md",
      "score": 0.87,
      "content": "..."
    }
  ]
}
```

---

## 8. AGENTS.md в каждом репозитории

В каждом проекте должен быть файл `AGENTS.md`.

Шаблон:

```markdown
# AGENTS.md

## Project
Название и краткое описание проекта.

## Setup
```bash
...
```

## Development
```bash
...
```

## Tests
```bash
...
```

## Lint
```bash
...
```

## Architecture
Кратко описать основные директории и модули.

## Rules
- Не менять production env без подтверждения.
- Не делать force push.
- Не удалять миграции без подтверждения.
- Все изменения делать в отдельной ветке.
- Перед завершением задачи запускать тесты.

## Deployment
Ссылка на memory-файл:
`/opt/agent-control/memory/projects/<project>/deployment.md`

## Known Problems
- ...
```

---

## 9. Модель данных Orchestrator API

### 9.1 Projects

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    repo_path TEXT NOT NULL,
    memory_path TEXT NOT NULL,
    default_branch TEXT NOT NULL DEFAULT 'main',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 9.2 Agents

```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    model TEXT NULL,
    permissions JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 9.3 Telegram topics

```sql
CREATE TABLE telegram_topics (
    id UUID PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    message_thread_id BIGINT NULL,
    title TEXT NOT NULL,
    kind TEXT NOT NULL,
    agent_id UUID NULL REFERENCES agents(id),
    project_id UUID NULL REFERENCES projects(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(chat_id, message_thread_id)
);
```

### 9.4 Tasks

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    external_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    risk_level TEXT NOT NULL DEFAULT 'low',
    project_id UUID NULL REFERENCES projects(id),
    agent_id UUID NULL REFERENCES agents(id),
    telegram_chat_id BIGINT NULL,
    telegram_thread_id BIGINT NULL,
    created_by BIGINT NULL,
    branch_name TEXT NULL,
    worktree_path TEXT NULL,
    result_summary TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 9.5 Approvals

```sql
CREATE TABLE approvals (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    requested_by_agent_id UUID NULL REFERENCES agents(id),
    approved_by BIGINT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    decided_at TIMESTAMPTZ NULL
);
```

---

## 10. Права агентов

### 10.1 Уровни риска

```text
low      → чтение, анализ, план, простые изменения в ветке
medium   → запуск тестов, изменение кода, создание PR, staging deploy
high     → миграции, изменение env, restart сервисов
critical → production deploy, удаление данных, изменение DNS, секреты
```

### 10.2 Политика разрешений

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
  "delete_files": "approval_required"
}
```

### 10.3 Жесткие запреты

Агенты не должны иметь прямой доступ к:

- root shell без sandbox;
- приватным SSH-ключам;
- production `.env` в открытом виде;
- billing/API keys;
- удалению production database;
- `rm -rf` вне рабочей директории;
- force push;
- прямому merge в main без approval.

---

## 11. Рабочий цикл задачи

### 11.1 Основной flow

```text
1. Пользователь пишет задачу в Telegram.
2. Bot Gateway принимает сообщение.
3. Orchestrator определяет agent, project, intent, risk_level.
4. Создается запись task.
5. Retrieval API подгружает память проекта.
6. Agent Runtime Adapter создает OpenCode-сессию.
7. Агент сначала возвращает план.
8. Если задача требует write/deploy — бот просит approve.
9. После approve создается git branch/worktree.
10. Агент выполняет изменения.
11. Запускаются тесты/lint.
12. Формируется summary.
13. Создается PR или diff.
14. Бот отправляет результат в Telegram.
15. Task summary записывается в memory/runs и project/agent-notes.md.
16. Индексатор обновляет retrieval memory.
```

### 11.2 Правило plan-first

Любая задача, которая может изменить код, инфраструктуру или данные, должна сначала пройти режим plan.

Формат ответа агента:

```markdown
## Plan
1. ...
2. ...
3. ...

## Files likely to change
- ...

## Commands to run
- ...

## Risks
- ...

## Requires approval
yes/no
```

---

## 12. Git workflow

Для каждой задачи:

```text
main/develop
    ↓
git worktree add /opt/agent-control/worktrees/<task-id> -b agent/<task-id>
    ↓
agent changes
    ↓
tests
    ↓
commit
    ↓
PR
```

Команды:

```bash
git fetch --all
git checkout main
git pull
git worktree add /opt/agent-control/worktrees/task-0001 -b agent/task-0001
```

После завершения:

```bash
git status
git diff --stat
git add .
git commit -m "agent: implement <task>"
git push origin agent/task-0001
```

---

## 13. Docker sandbox

Агент должен выполнять команды внутри sandbox-контейнера, а не напрямую на хосте.

Пример:

```yaml
services:
  agent-sandbox:
    image: agent-sandbox-python:3.12
    working_dir: /workspace
    volumes:
      - /opt/agent-control/worktrees/task-0001:/workspace
    environment:
      - ENV=development
    networks:
      - agent_net
    mem_limit: 2g
    cpus: 2
```

Запуск:

```bash
docker compose -f sandbox.compose.yml run --rm agent-sandbox pytest
```

---

## 14. Deploy pipeline

### 14.1 Staging deploy

Можно разрешить агентам после прохождения тестов.

```text
agent changes
    ↓
tests passed
    ↓
staging deploy
    ↓
smoke test
    ↓
telegram report
```

### 14.2 Production deploy

Только через approval.

```text
agent requests production deploy
    ↓
bot sends approval card
    ↓
user approves
    ↓
backup if needed
    ↓
production deploy
    ↓
smoke test
    ↓
telegram report
```

### 14.3 Approval card в Telegram

```text
Production deploy request
Project: academy-bot
Task: task-0001
Branch: agent/task-0001
Risk: high
Tests: passed
Migrations: no
Env changes: no

[Approve deploy] [Reject] [Show diff]
```

---

## 15. OpenCode integration

### 15.1 Роль OpenCode

OpenCode используется для:

- анализа репозитория;
- выполнения coding-задач;
- работы с файлами;
- запуска команд;
- применения инструкций из `AGENTS.md`;
- работы через server/API/SDK.

### 15.2 Adapter interface

Нужно сделать внутренний интерфейс, чтобы в будущем можно было заменить OpenCode на другой runtime.

```python
class AgentRuntimeAdapter:
    async def create_session(self, task, project, agent):
        raise NotImplementedError

    async def send_message(self, session_id: str, message: str):
        raise NotImplementedError

    async def stream_events(self, session_id: str):
        raise NotImplementedError

    async def stop_session(self, session_id: str):
        raise NotImplementedError
```

### 15.3 Prompt для запуска задачи

```markdown
You are {agent_name}.

Role:
{agent_role}

Project:
{project_name}

Task:
{task_text}

Relevant memory:
{retrieved_memory}

Rules:
- First produce a plan.
- Do not modify files before approval if task risk is medium/high/critical.
- Use AGENTS.md as the source of project-specific rules.
- Work only inside the assigned worktree.
- Do not access secrets.
- Before completion, run required tests if possible.
- Return summary, changed files, commands run, risks, and next steps.
```

---

## 16. MCP-like слой для памяти

Так как нужна память по аналогии с Obsidian MCP, стоит сделать внутренний Memory MCP Server или MCP-compatible сервис.

Минимальные tools:

```text
memory.search(query, project_slug?)
memory.read(path)
memory.write(path, content)
memory.append(path, content)
memory.link(from_path, to_path, relation)
project.list()
project.get(slug)
project.commands(slug)
project.deployment(slug)
task.create(...)
task.update(...)
approval.request(...)
```

Важно: агентам нельзя давать свободную запись во все файлы памяти. Для записи нужны правила.

Разрешить:

```text
memory/projects/<project>/agent-notes.md
memory/projects/<project>/tasks.md
memory/runs/<date-task>.md
```

Через approval:

```text
memory/projects/<project>/deployment.md
memory/global/security-rules.md
memory/global/infrastructure.md
```

---

## 17. API endpoints MVP

```text
POST   /telegram/webhook
GET    /health

GET    /projects
POST   /projects
GET    /projects/{slug}
PATCH  /projects/{slug}

GET    /agents
POST   /agents
GET    /agents/{slug}
PATCH  /agents/{slug}

POST   /tasks
GET    /tasks/{id}
POST   /tasks/{id}/approve
POST   /tasks/{id}/reject
POST   /tasks/{id}/cancel

POST   /memory/search
GET    /memory/file?path=...
POST   /memory/reindex

POST   /runtime/sessions
GET    /runtime/sessions/{id}/events
POST   /runtime/sessions/{id}/stop
```

---

## 18. Очереди задач

Очереди:

```text
telegram_inbound
agent_plan
agent_execute
memory_index
deploy_staging
deploy_production
notifications
```

Task statuses:

```text
created
routed
planning
waiting_approval
approved
running
tests_running
pr_created
deploying_staging
deploying_production
completed
failed
cancelled
```

---

## 19. Логи и audit trail

Каждое действие агента логировать.

```sql
CREATE TABLE task_events (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    actor_id TEXT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Примеры событий:

```text
message_received
agent_selected
project_selected
memory_retrieved
plan_generated
approval_requested
approval_granted
worktree_created
command_started
command_finished
file_changed
tests_passed
tests_failed
pr_created
deploy_started
deploy_finished
task_completed
task_failed
```

---

## 20. Репозиторий системы

```text
agent-mission-control/
  apps/
    api/
      app/
        main.py
        config.py
        db/
        models/
        routers/
        services/
        workers/
        integrations/
          telegram/
          opencode/
          github/
          docker/
        memory/
        security/
      pyproject.toml

    bot/
      app/
        main.py
        handlers/
        keyboards/
        middlewares/
      pyproject.toml

    worker/
      app/
        main.py
        queues/
        jobs/
      pyproject.toml

    web/
      src/
      package.json

  packages/
    shared/

  infra/
    docker-compose.yml
    docker-compose.prod.yml
    nginx/
    systemd/

  memory/
    global/
    projects/
    agents/
    runs/

  scripts/
    init_project.py
    reindex_memory.py
    create_agent.py
    create_topic_map.py

  docs/
    architecture.md
    telegram.md
    memory.md
    deployment.md
    security.md

  .env.example
  README.md
  AGENTS.md
```

---

## 21. MVP roadmap

### Phase 0: подготовка

Результат: сервер готов, репозиторий создан.

Задачи:

- создать mono-repo;
- поднять PostgreSQL + Redis;
- настроить FastAPI;
- настроить aiogram webhook или long polling;
- создать Telegram group с topics;
- добавить таблицы projects, agents, topics, tasks.

### Phase 1: Telegram routing

Результат: сообщения из топиков превращаются в задачи.

Задачи:

- принимать Telegram updates;
- сохранять `chat_id` и `message_thread_id`;
- создать ручную привязку topic → agent/project;
- сделать `/projects`, `/agents`, `/task`;
- отправлять ответы обратно в нужный топик.

### Phase 2: Project memory

Результат: у каждого проекта есть markdown-память.

Задачи:

- создать структуру `/memory`;
- сделать CRUD для memory files;
- сделать indexer markdown-файлов;
- подключить pgvector или Qdrant;
- реализовать `/memory/search`;
- добавить summary после каждой задачи в `memory/runs` и `agent-notes.md`.

### Phase 3: OpenCode runtime

Результат: агент может создать план по задаче.

Задачи:

- поднять OpenCode server;
- сделать OpenCode adapter;
- передавать агенту задачу + retrieved memory + AGENTS.md;
- получить план;
- отправить план в Telegram.

### Phase 4: Safe code execution

Результат: агент может менять код в отдельной ветке.

Задачи:

- реализовать git worktree per task;
- запускать команды в Docker sandbox;
- собирать diff;
- запускать tests/lint;
- отправлять summary в Telegram.

### Phase 5: PR workflow

Результат: агент создает PR.

Задачи:

- GitHub/GitLab integration;
- push branch;
- create PR/MR;
- attach summary;
- save PR link в task.

### Phase 6: Deploy staging

Результат: агент может деплоить staging.

Задачи:

- описать deploy commands в memory;
- реализовать deploy job;
- сделать smoke tests;
- отправлять результат в Telegram.

### Phase 7: Production approval

Результат: production deploy только после approve.

Задачи:

- approval cards;
- audit log;
- production deploy job;
- rollback command;
- deploy report.

### Phase 8: Web dashboard

Результат: интерфейс в стиле Mission Control.

Задачи:

- React dashboard;
- список агентов;
- task queue;
- system status;
- project cards;
- live logs через SSE/WebSocket;
- настройки прав агентов.

---

## 22. Команды для агентов

### `/new_project`

Создать проект в системе.

```text
/new_project slug=academy-bot repo=/opt/agent-control/repos/academy-bot stack=python-fastapi
```

Действия:

- создать запись в `projects`;
- создать memory folder;
- создать шаблонные md-файлы;
- проверить наличие `AGENTS.md`;
- запустить первичную индексацию.

### `/agent`

Создать или вызвать агента.

```text
/agent backend project=academy-bot task="добавь healthcheck"
```

### `/plan`

Только план без выполнения.

```text
/plan project=academy-bot agent=backend добавь webhook status endpoint
```

### `/run`

Выполнить после approve.

```text
/run task=task-0001
```

### `/memory`

Работа с памятью.

```text
/memory search project=academy-bot query="как деплоить staging"
/memory append project=academy-bot file=agent-notes.md text="..."
```

### `/deploy`

```text
/deploy project=academy-bot env=staging branch=agent/task-0001
/deploy project=academy-bot env=production branch=main
```

Production должен создавать approval request.

---

## 23. Prompt для системного orchestrator-agent

```markdown
You are the Orchestrator Agent for Agent Mission Control.

Your job:
- classify incoming Telegram messages;
- identify project, agent, intent, and risk level;
- decide whether the task needs plan-only, approval, execution, or rejection;
- never execute code directly;
- create structured tasks for specialized agents;
- use project memory before assigning work;
- keep responses short and actionable.

Risk rules:
- Reading and planning is low risk.
- Code changes are medium risk.
- Staging deploy is medium risk.
- Production deploy is high risk.
- DB migrations, env changes, restarts are high risk.
- Deleting data, touching secrets, force push, root commands are critical risk.

Always return JSON:
{
  "intent": "...",
  "project_slug": "...",
  "agent_slug": "...",
  "risk_level": "low|medium|high|critical",
  "requires_approval": true,
  "task_title": "...",
  "normalized_task": "..."
}
```

---

## 24. Prompt для backend-agent

```markdown
You are Backend Agent.

Responsibilities:
- Python backend
- FastAPI/Django/aiohttp services
- Telegram bots
- databases
- API integrations
- tests

Rules:
- Read AGENTS.md first.
- Read project memory before changing code.
- Work only in assigned worktree.
- Do not touch production secrets.
- Write tests for meaningful behavior changes.
- Run tests before final answer when possible.
- Summarize changed files and commands.
```

---

## 25. Prompt для frontend-agent

```markdown
You are Frontend Agent.

Responsibilities:
- React
- Next.js/Vite
- TailwindCSS
- UI components
- API integration
- frontend tests

Rules:
- Read AGENTS.md first.
- Preserve existing UI patterns.
- Do not introduce heavy dependencies without approval.
- Run lint/build when possible.
- Summarize changed files and commands.
```

---

## 26. Prompt для devops-agent

```markdown
You are DevOps Agent.

Responsibilities:
- Docker
- Compose
- CI/CD
- Nginx/Caddy
- deployments
- logs
- monitoring

Rules:
- Production actions require approval.
- Env changes require approval.
- DB migrations require approval.
- Never print secrets.
- Always provide rollback steps for deploy-related tasks.
- Prefer staging before production.
```

---

## 27. Что нельзя делать в MVP

Не делать сразу:

- полную автономность без approvals;
- production deploy без человека;
- root-доступ агентам;
- доступ агентам ко всем секретам;
- сложную multi-agent дискуссию без пользы;
- web UI раньше Telegram MVP;
- автоматическое изменение глобальной памяти без audit log.

---

## 28. Definition of Done для MVP

MVP считается готовым, если:

- Telegram bot принимает сообщения из forum topics;
- topic корректно маппится на агента или проект;
- можно зарегистрировать проект;
- для проекта создается markdown memory vault;
- memory индексируется и доступна через search;
- агент может получить задачу и вернуть plan;
- агент может выполнить approved-задачу в git worktree;
- команды запускаются в sandbox;
- бот возвращает diff summary и test result;
- результат задачи записывается в memory;
- production deploy невозможен без approval.

---

## 29. Первый конкретный спринт

### Sprint 1 goal

Собрать Telegram-first каркас без реального выполнения кода агентом.

### Tasks

1. Создать repo `agent-mission-control`.
2. Поднять FastAPI.
3. Поднять PostgreSQL и Redis через Docker Compose.
4. Создать модели: Project, Agent, TelegramTopic, Task, TaskEvent.
5. Создать Telegram bot через BotFather.
6. Подключить bot к forum group.
7. Научиться получать `message_thread_id`.
8. Сделать ручную команду `/bind_topic agent backend`.
9. Сделать создание task из сообщения.
10. Сделать ответ бота в тот же topic.
11. Создать `/memory/projects/<slug>` при добавлении проекта.
12. Сделать базовый markdown writer.
13. Сделать task summary writer.

### Sprint 1 output

- Рабочий Telegram bot.
- Сообщение в топике создает task.
- Task сохраняется в PostgreSQL.
- Bot отвечает в тот же topic.
- У проекта есть папка памяти.

---

## 30. Второй конкретный спринт

### Sprint 2 goal

Добавить память и plan-only агента.

### Tasks

1. Реализовать markdown indexer.
2. Подключить pgvector или Qdrant.
3. Реализовать `/memory/search`.
4. Поднять OpenCode server.
5. Сделать OpenCode adapter.
6. Передавать в agent prompt:
   - task text;
   - project memory;
   - AGENTS.md;
   - правила безопасности.
7. Получать plan.
8. Отправлять plan в Telegram.
9. Создавать approval request для medium/high задач.

### Sprint 2 output

- Агент отвечает планом на основе памяти проекта.
- Код еще не меняется без approve.

---

## 31. Третий конкретный спринт

### Sprint 3 goal

Разрешить безопасное выполнение задач в worktree.

### Tasks

1. Git worktree per task.
2. Docker sandbox per task.
3. Approved execution.
4. Run tests.
5. Diff summary.
6. Commit changes.
7. Optional PR creation.
8. Write memory run summary.

### Sprint 3 output

- Агент может выполнить простую coding-задачу и вернуть результат.

---

## 32. Источники и проверочные ссылки

Для агентов, которые будут валидировать реализацию:

- OpenCode docs: server, SDK, agents, rules, AGENTS.md.
- Telegram Bot API: `message_thread_id` для forum topics.
- python-telegram-bot / aiogram docs: работа с forum topics.
- AGENTS.md open format: структура инструкций для coding agents.
- OpenChamber GitHub: пример web/desktop интерфейса поверх OpenCode.

---

## 33. Короткое резюме для агентов

Строить нужно не просто чат-бота, а orchestration platform:

```text
Telegram = UI
FastAPI = control plane
PostgreSQL = state
Redis = queue
Markdown vault = long-term project memory
pgvector/Qdrant = semantic retrieval
OpenCode = coding runtime
Docker = sandbox
Git worktree = isolated changes
GitHub/GitLab = PR workflow
Approval system = safety layer
React dashboard = later
```

Критически важно:

- сначала Telegram MVP;
- затем память;
- затем OpenCode plan-only;
- затем safe execution;
- затем staging deploy;
- затем production approval;
- dashboard — после стабильного backend.
