# CHANGELOG.md — История изменений проекта

## 2026-05-03

### Project Root Correction
- Вся документация перенесена в `F:\dev\agentrouter`
- `.ai_memory/` инициализирован как главный Obsidian-like vault
- 34 файла созданы в правильном project root
- Структура: `.ai_memory/` (master vault) + `docs/` (статическая документация)

### Documentation Bootstrap (Phase 0)
- Спроектирована архитектура системы (3 слоя)
- Определена структура monorepo
- Спроектирована схема БД (8 таблиц)
- Составлен roadmap из 8 фаз
- Написаны 4 Architecture Decision Records
- Создан MVP backlog с 25 задачами (docs/mvp-backlog.md)

### FND-01: Repo Bootstrap (git-workflow-master)
- `.gitignore` — Python/Node/Docker/IDE/OS
- `CHANGELOG.md` — этот файл
- `CONTRIBUTING.md` — правила для контрибьюторов
- `docs/git-workflow.md` — git-стратегия проекта

### FND-02: API Skeleton (backend-architect)
- `apps/api/app/main.py` — FastAPI приложение, lifespan, CORS, /health
- `apps/api/app/config.py` — pydantic-settings конфигурация
- `apps/api/pyproject.toml` — Python-проект с зависимостями
