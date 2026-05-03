# Task Summary: MEM-01 — Memory Provisioning

**Дата:** 2026-05-03
**Агент:** knowledge-steward
**Статус:** ✅ Выполнена

---

## Цель

Создать систему provisioning для памяти проектов внутри `.ai_memory/` vault: шаблоны, сервис, схемы, документация.

## Что сделано

### Backend (apps/api/)

- **`app/services/memory_provisioning_service.py`** — `MemoryProvisioningService`:
  - `provision_project(slug, name)` → создаёт 7 файлов, не перезаписывает существующие
  - `get_project_info(slug)` → информация о vault проекта
  - `list_projects()` → список всех проектов с vault
  - Использует `PROJECT_FILES` dict с 7 template functions

- **`app/schemas/memory.py`** — Pydantic схемы:
  - `MemoryProvisionRequest(slug, name)` с валидацией slug
  - `MemoryProvisionResult(slug, project_dir, files)` с `created_count`/`skipped_count`
  - `MemoryFileResult(filename, status, path)`
  - `MemoryProjectInfo(slug, project_dir, files, exists)`
  - `contains_forbidden_content(text)` — детекция secrets (assignment-based patterns)

### Templates (.ai_memory/templates/)

- **`project-memory-template.md`** — обновлён: 7 файлов (overview, current_state, architecture, decisions, tasks, known_issues, agent_notes)
- **`task-summary-template.md`** — обновлён
- **`agent-notes-template.md`** — новый
- **`adr-template.md`** — обновлён
- **`current-state-template.md`** — новый

### Vault docs (.ai_memory/)

- **`README.md`** — обновлён: правила vault, write access tiers, secrets ban
- **`_INDEX.md`** — обновлён: 5 templates, 12 task logs, 4 ADRs
- **`projects/README.md`** — обновлён: 7-file структура + provisioning info

### Documentation

- **`docs/memory-system.md`** — новый: полное руководство для агентов

### Tests

- **`tests/test_memory_provisioning.py`** — 12 тестов:
  - provision creates 7 files
  - does not overwrite existing
  - template substitution (slug, name)
  - get_project_info (existing, nonexistent)
  - list_projects (empty, after provision)
  - PROJECT_FILES constant has 7 entries
  - schema slug validation (valid, rejects bad)
  - forbidden content detection (secrets vs normal text)
  - auto-creates projects/ dir

## 7 файлов памяти проекта

| Файл | Назначение |
|------|-----------|
| `overview.md` | Описание, стек, repo, owner, production/staging |
| `current_state.md` | Текущий статус, фаза, блокеры |
| `architecture.md` | Архитектура, модули, data flow |
| `decisions.md` | ADR (архитектурные решения) |
| `tasks.md` | Активные и завершённые задачи |
| `known_issues.md` | Проблемы и риски |
| `agent_notes.md` | Заметки агентов после задач |

## Проверки

| Проверка | Результат |
|----------|-----------|
| `compileall` | ✅ Clean |
| `ruff` | ✅ All checks passed |
| `pytest` (API total) | ✅ 64/64 |
| `pytest` (MEM-01 only) | ✅ 12/12 |

## Ограничения соблюдены

- ❌ Не создавался memory/ в корне
- ❌ Не делался Docker
- ❌ Не делался deploy
- ❌ Не менялся .env/secrets
- ❌ Не запускались миграции
- ❌ Не подключался к production/staging
- ❌ Не запускались агенты/OpenCode
- ❌ Не работал вне F:\dev\agentrouter

## Следующие шаги

- **MEM-03:** Memory indexing + retrieval (pgvector, chunker, embedder, /memory/search)
- **DOP-02:** Dockerfiles + sandbox compose
- **WRK-03:** Execute pipeline
