# Task Summary: MEM-03 — Memory indexing + retrieval

**Дата:** 2026-05-03  
**Агент:** backend-architect  
**Статус:** ✅ Выполнена

---

## Цель

Реализовать безопасную индексацию markdown-файлов из `.ai_memory` и retrieval API без реальных внешних embedding-провайдеров.

## Что сделано

### API services

- `apps/api/app/services/memory_chunking_service.py`
  - heading-aware chunking
  - fallback разбивка по размеру
  - `chunk_index` и metadata-friendly drafts

- `apps/api/app/services/memory_embedding_service.py`
  - deterministic fake embeddings (1536)
  - `DeterministicEmbeddingProvider`
  - `cosine_similarity`

- `apps/api/app/services/memory_indexing_service.py`
  - scan только `.ai_memory/**/*.md`
  - skip `.obsidian`, hidden, non-md, outside-vault
  - hash-based skip unchanged docs
  - scope/project_slug resolution (`projects/<slug>/...`)
  - безопасная замена старых chunks (delete old → insert new)
  - metadata per chunk: `path`, `title`, `scope`, `project_slug`, `heading`

- `apps/api/app/services/memory_retrieval_service.py`
  - retrieval protocol + SQLAlchemy repo
  - top-k ranking by cosine similarity
  - filters by `scope[]` and `project_slug`

### API schemas + router

- `apps/api/app/schemas/memory.py`
  - `MemorySearchRequest`, `MemorySearchItem`, `MemorySearchResponse`
  - `MemoryReindexRequest`, `MemoryReindexResponse`

- `apps/api/app/routers/memory.py`
  - `POST /memory/reindex`
  - `POST /memory/search`
  - MEM-02 endpoints сохранены

### Worker

- `apps/worker/app/tasks/memory_index.py`
  - вместо stub вызывает `POST {API_BASE_URL}/memory/reindex`
  - возвращает counters: `scanned_files`, `indexed_documents`, `skipped_documents`, `total_chunks`
  - HTTP error path возвращает structured payload

## Тесты

- `apps/api/tests/test_memory_chunking.py`
- `apps/api/tests/test_memory_retrieval.py` (fake repository)
- `apps/api/tests/test_memory_router.py` (reindex/search tests + async session override)
- `apps/worker/tests/test_tasks.py` (memory_index success/error)

## Проверки

- API full: `147/147` ✅
- Worker full: `27/27` ✅
- compileall ✅
- ruff ✅

## Ограничения соблюдены

- Без deploy/migrations
- Без .env/secrets изменений
- Без production/staging подключений
- Работа только в `F:\dev\agentrouter`

## Следующие шаги

1. Тюнинг retrieval ranking (weights/heuristics)
2. Добавить retrieval explain/debug fields при необходимости
