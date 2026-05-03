# Схема базы данных — Agent Mission Control

Версия: 1.0
Дата: 2026-05-03
БД: PostgreSQL 16 + pgvector

## ER-диаграмма

```
projects ──────────┐
                   │
agents ────────────┤
                   │
telegram_topics ───┤──→ tasks ──→ approvals
                   │        └──→ task_events
memory_documents ──┤
                   │
memory_chunks ─────┘
```

## Таблицы

### 1. projects

Проекты пользователя, привязанные к git-репозиториям.

```sql
CREATE TABLE projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug            TEXT UNIQUE NOT NULL,
    name            TEXT NOT NULL,
    repo_path       TEXT NOT NULL,
    memory_path     TEXT NOT NULL,
    default_branch  TEXT NOT NULL DEFAULT 'main',
    status          TEXT NOT NULL DEFAULT 'active',
    stack           JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 2. agents

Агенты системы с ролями и разрешениями.

```sql
CREATE TABLE agents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug            TEXT UNIQUE NOT NULL,
    name            TEXT NOT NULL,
    role            TEXT NOT NULL,
    system_prompt   TEXT NOT NULL,
    model           TEXT DEFAULT NULL,
    permissions     JSONB NOT NULL DEFAULT '{}',
    status          TEXT NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 3. telegram_topics

Привязка Telegram topics к агентам, проектам или системным функциям.

```sql
CREATE TABLE telegram_topics (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id             BIGINT NOT NULL,
    message_thread_id   BIGINT NOT NULL,
    title               TEXT NOT NULL,
    kind                TEXT NOT NULL,
    agent_id            UUID REFERENCES agents(id) ON DELETE SET NULL,
    project_id          UUID REFERENCES projects(id) ON DELETE SET NULL,
    is_active           BOOLEAN NOT NULL DEFAULT true,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(chat_id, message_thread_id)
);

CREATE INDEX idx_telegram_topics_chat ON telegram_topics(chat_id);
CREATE INDEX idx_telegram_topics_kind ON telegram_topics(kind);
```

### 4. tasks

Задачи, созданные из Telegram или API.

```sql
CREATE TABLE tasks (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id         TEXT UNIQUE NOT NULL,
    title               TEXT NOT NULL,
    raw_text            TEXT NOT NULL,
    normalized_text     TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'created',
    risk_level          TEXT NOT NULL DEFAULT 'low',
    intent              TEXT,
    project_id          UUID REFERENCES projects(id) ON DELETE SET NULL,
    agent_id            UUID REFERENCES agents(id) ON DELETE SET NULL,
    telegram_chat_id    BIGINT,
    telegram_thread_id  BIGINT,
    created_by          BIGINT,
    branch_name         TEXT,
    worktree_path       TEXT,
    plan_text           TEXT,
    result_summary      TEXT,
    payload             JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_agent ON tasks(agent_id);
CREATE INDEX idx_tasks_created ON tasks(created_at DESC);
```

**Task status flow:**

```
created → routed → planning → waiting_approval → approved → running
    → tests_running → pr_created → deploying_staging → completed
                                                              ↓
                                                         failed
                                                         cancelled
```

### 5. approvals

Подтверждения для опасных действий.

```sql
CREATE TABLE approvals (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id                 UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    action                  TEXT NOT NULL,
    status                  TEXT NOT NULL DEFAULT 'pending',
    requested_by_agent_id   UUID REFERENCES agents(id) ON DELETE SET NULL,
    approved_by             BIGINT,
    reason                  TEXT,
    payload                 JSONB NOT NULL DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    decided_at              TIMESTAMPTZ NULL
);

CREATE INDEX idx_approvals_task ON approvals(task_id);
CREATE INDEX idx_approvals_status ON approvals(status);
```

### 6. task_events

Audit trail — логирование всех действий по задаче.

```sql
CREATE TABLE task_events (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id     UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    event_type  TEXT NOT NULL,
    actor_type  TEXT NOT NULL,
    actor_id    TEXT,
    payload     JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_task_events_task ON task_events(task_id);
CREATE INDEX idx_task_events_type ON task_events(event_type);
CREATE INDEX idx_task_events_created ON task_events(created_at DESC);
```

### 7. memory_documents

Индексированные документы памяти.

```sql
CREATE TABLE memory_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scope           TEXT NOT NULL,
    project_id      UUID REFERENCES projects(id) ON DELETE CASCADE,
    path            TEXT NOT NULL,
    title           TEXT,
    content         TEXT NOT NULL,
    content_hash    TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_memory_docs_path ON memory_documents(scope, project_id, path);
```

### 8. memory_chunks

Чанки документов с векторными embeddings.

```sql
CREATE TABLE memory_chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES memory_documents(id) ON DELETE CASCADE,
    project_id      UUID REFERENCES projects(id) ON DELETE SET NULL,
    chunk_index     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    embedding       VECTOR(1536),
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_memory_chunks_project ON memory_chunks(project_id);
CREATE INDEX idx_memory_chunks_embedding ON memory_chunks
    USING ivfflat (embedding vector_cosine_ops);
```
