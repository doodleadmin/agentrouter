# Task Summary: MEM-02 — Memory CRUD API + Policy Guard

**Дата:** 2026-05-03  
**Агент:** backend-architect  
**Статус:** ✅ Выполнена

---

## Цель

Реализовать безопасный CRUD-слой для `.ai_memory` через backend API: чтение/запись markdown-файлов, provision проекта, policy-валидация путей, контроль уровней доступа и блокировка секретов.

## Что сделано

### 1) Policy service

Файл: `apps/api/app/services/memory_policy_service.py`

- Добавлены уровни доступа `AccessTier`:
  - `free`
  - `approval_required`
  - `forbidden`
- Реализована валидация пути `validate_memory_path()`:
  - блок `..` traversal
  - блок абсолютных путей (`/`)
  - блок Windows-drive (`C:`)
  - блок backslash (`\`)
  - разрешены только `.md`
- Реализованы правила tier-ов через `get_write_tier()`:
  - **FREE:** `tasks/*`, `projects/*/agent_notes.md`, `projects/*/current_state.md`, `projects/*/tasks.md`, `projects/*/known_issues.md`
  - **APPROVAL_REQUIRED:** root `README.md`, `_INDEX.md`, `current_state.md`; `projects/*/overview.md|architecture.md|decisions.md`; `decisions/*`; `agents/*`
  - **FORBIDDEN:** `.obsidian/*`, `templates/*`
- Реализована проверка записи `check_write_allowed()` с детекцией секретов.
- Кастомные исключения:
  - `PathValidationError`
  - `SecretsDetectedError`
  - `WriteForbiddenError`

### 2) Memory service

Файл: `apps/api/app/services/memory_service.py`

- Реализованы операции:
  - `read_file(relative_path)`
  - `write_file(relative_path, content, bypass_approval=False)`
  - `append_file(relative_path, content, bypass_approval=False)`
  - `list_files(prefix=None, project_slug=None)`
  - `get_access_tier(relative_path)`
- Чтение/запись работают только внутри `settings.MEMORY_VAULT_PATH`.
- Для отсутствующего файла добавлено `MemoryFileNotFoundError`.

### 3) Schemas

Файл: `apps/api/app/schemas/memory.py`

- Добавлены CRUD-схемы:
  - `MemoryFileRead`
  - `MemoryFileWriteRequest`
  - `MemoryFileWrite`
  - `MemoryFileListResult`
  - `MemoryAccessInfo`
- Для provisioning-результата:
  - `MemoryProvisionResult.created_count` и `skipped_count` через `@computed_field`

### 4) Router

Файл: `apps/api/app/routers/memory.py`

Добавлены endpoint-ы:

1. `GET /memory/files`
2. `GET /memory/files/{path:path}`
3. `PUT /memory/files/{path:path}`
4. `POST /memory/files/{path:path}/append`
5. `POST /memory/projects/{slug}/provision`
6. `GET /memory/access?path=...`

Плюс: router зарегистрирован в `main.py` и `routers/__init__.py`.

---

## Тесты

Добавлено 76 новых тестов:

- `apps/api/tests/test_memory_policy.py` — 35
- `apps/api/tests/test_memory_service.py` — 20
- `apps/api/tests/test_memory_router.py` — 17
- + корректировки существующих для MEM-02

## Результаты проверок

- `python -m compileall app` ✅
- `ruff check app` ✅
- `pytest tests/test_memory_policy.py tests/test_memory_service.py tests/test_memory_router.py -v` ✅ (76/76)
- `pytest tests -v` ✅ (140/140)

---

## Ограничения соблюдены

- Не выполнялись deploy/staging/prod действия
- Не запускались миграции
- Не менялись `.env`/secrets
- Работа только в `F:\dev\agentrouter`

## Следующие шаги

1. MEM-03: memory indexing + retrieval (`/memory/search`, embeddings, pgvector)
2. WRK-03: execute pipeline
