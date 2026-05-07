# Memory System

> Документ описывает, как агенты читают и обновляют память проекта через `.ai_memory/` vault.

---

## Обзор

Agent Mission Control использует **Obsidian-like markdown vault** в `.ai_memory/` как единственный source of truth для памяти проектов.

Vault НЕ является базой данных. Это набор Markdown-файлов, которые:
- Читаются людьми напрямую (в Obsidian, VS Code, GitHub)
- Читаются агентами через файловую систему
- Индексируются для semantic retrieval (MEM-03)
- Управляются через `MemoryProvisioningService`

---

## Структура vault

```text
.ai_memory/
├── README.md                 ← Правила vault
├── _INDEX.md                 ← Навигация (обновляется автоматически)
├── current_state.md          ← Глобальный статус системы
│
├── projects/
│   └── <project-slug>/       ← 7 файлов на проект
│       ├── overview.md           Описание, стек, repo, owner
│       ├── current_state.md      Активный статус проекта
│       ├── architecture.md       Архитектура, модули
│       ├── decisions.md          Архитектурные решения
│       ├── tasks.md              Задачи
│       ├── known_issues.md       Проблемы и риски
│       └── agent_notes.md        Заметки агентов
│
├── agents/                   ← Профили агентов (опционально)
├── tasks/                    ← Task summaries (по одному файлу на задачу)
├── decisions/                ← ADR (Architecture Decision Records)
└── templates/                ← Шаблоны для provisioning
```

---

## Source of Truth

| Файл | Кто пишет | Когда |
|------|-----------|-------|
| `projects/*/overview.md` | Агенты (через approve) | При первом контакте с проектом |
| `projects/*/current_state.md` | Любой агент | После каждой задачи |
| `projects/*/architecture.md` | Агенты (через approve) | При изменении архитектуры |
| `projects/*/decisions.md` | Агенты (через approve) | При принятии ADR |
| `projects/*/tasks.md` | Любой агент | При создании/завершении задачи |
| `projects/*/known_issues.md` | Любой агент | При обнаружении проблемы |
| `projects/*/agent_notes.md` | Любой агент | После каждой задачи |
| `tasks/*.md` | Любой агент | После завершения задачи |
| `current_state.md` | Любой агент | После каждой задачи |
| `_INDEX.md` | System / knowledge-steward | При изменении структуры |

---

## Как агенты читают память

### Обязательное чтение (cold start)

Каждый агент при старте сессии должен прочитать:

1. `PROJECT_MEMORY.md` — краткий индекс
2. `.ai_memory/current_state.md` — глобальный статус
3. `.ai_memory/_INDEX.md` — навигация

### Чтение по проекту

При работе с конкретным проектом:

1. `.ai_memory/projects/<slug>/overview.md` — что за проект
2. `.ai_memory/projects/<slug>/current_state.md` — текущий статус
3. `.ai_memory/projects/<slug>/architecture.md` — как устроен
4. `.ai_memory/projects/<slug>/agent_notes.md` — что уже делали

### Чтение по задаче

При работе над задачей:

1. `.ai_memory/tasks/<task-file>.md` — task summary
2. `.ai_memory/projects/<slug>/known_issues.md` — известные проблемы
3. `.ai_memory/projects/<slug>/decisions.md` — принятые решения

---

## Как агенты обновляют память

### После каждой задачи

1. **Создать task summary** в `.ai_memory/tasks/YYYY-MM-DD-task-<slug>.md`
2. **Обновить `current_state.md`** (глобальный)
3. **Добавить заметку** в `.ai_memory/projects/<slug>/agent_notes.md`
4. **Обновить `projects/<slug>/current_state.md`** если проект изменился

> **Memory checkpoint обязателен.** Задача не считается завершённой без memory checkpoint.
> Подробный runbook: [.ai_memory/runbooks/memory-checkpoint.md](../.ai_memory/runbooks/memory-checkpoint.md)

### При архитектурном решении

1. Создать ADR в `.ai_memory/decisions/00XX-<slug>.md`
2. Добавить секцию в `.ai_memory/projects/<slug>/decisions.md`
3. Обновить `current_state.md`

### При регистрации нового проекта

Использовать `MemoryProvisioningService.provision_project(slug, name)`:

```python
from app.services.memory_provisioning_service import MemoryProvisioningService

svc = MemoryProvisioningService()
result = svc.provision_project("my-project", "My Project")
# Создаёт 7 файлов в .ai_memory/projects/my-project/
```

---

## Правила записи

### Можно писать свободно (free)

- `tasks/*.md` — task summaries
- `projects/*/agent_notes.md` — заметки агентов
- `projects/*/tasks.md` — список задач
- `projects/*/current_state.md` — статус проекта
- `projects/*/known_issues.md` — проблемы

### Нужен approve

- `projects/*/overview.md` — описание проекта
- `projects/*/architecture.md` — архитектура
- `projects/*/decisions.md` — решения
- `decisions/*` — глобальные ADR
- `current_state.md` — глобальный статус

### Категорически запрещено

- **Secrets** — API tokens, passwords, private keys
- **Credentials** — database passwords, SSH keys, certificates
- **Raw logs** — большие объёмы сырых данных
- **Binary data** — файлы, не являющиеся Markdown

Если секрет обнаружен в данных — заменить на `[REDACTED]`.

---

## Forbidden content detection

Сервис `memory.py` содержит функцию `contains_forbidden_content()`:

```python
from app.schemas.memory import contains_forbidden_content

if contains_forbidden_content(text):
    # Не записывать! Заменить секреты на [REDACTED]
```

Обнаруживает: password, secret, token, api_key, apikey, private_key, credential, auth_token, access_token, refresh_token, session_id.

---

## Provisioning API

### Сервис

`MemoryProvisioningService` в `apps/api/app/services/`:

| Метод | Описание |
|-------|----------|
| `provision_project(slug, name)` | Создать 7 файлов памяти проекта |
| `get_project_info(slug)` | Получить информацию о vault проекта |
| `list_projects()` | Список всех проектов с vault |

### Schema

`MemoryProvisionRequest(slug, name)` — запрос на provisioning.
`MemoryProvisionResult(slug, project_dir, files)` — результат.
`MemoryFileResult(filename, status, path)` — статус одного файла.

---

## Indexing + Retrieval (MEM-03)

Реализовано:

- Markdown indexer + chunker
- Deterministic embedding provider (1536)
- `POST /memory/reindex` (ручной reindex)
- `POST /memory/search` (top-k retrieval)
- Worker task `memory_index` вызывает API reindex endpoint

Ограничения:

- Индексируются только `.ai_memory/**/*.md`
- `.obsidian/*`, скрытые и не-markdown файлы пропускаются
- Изменения определяются по `content_hash` (skip unchanged)
