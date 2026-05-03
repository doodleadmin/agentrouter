# CONTRIBUTING.md — Правила для разработчиков

## Project Root

Единственная рабочая папка: **`F:\dev\agentrouter`**

## Git Workflow

### Ветки
- `main` — production-ready код. Merge только через PR + approve.
- `develop` — integration ветка для staging.
- `agent/<task-id>` — feature-ветка на каждую задачу.

### Процесс
1. Создать ветку: `git checkout -b agent/<task-id>` (или worktree)
2. Внести изменения
3. Запустить тесты
4. Создать PR в `develop` или `main`
5. Дождаться approve и CI
6. Merge

### Коммиты
- Формат: `agent: <краткое описание>`
- Атомарные коммиты (одно изменение — один коммит)

### Git Worktree
Для изолированных задач на сервере:
```bash
git worktree add /opt/mc/worktrees/<task-id> -b agent/<task-id>
```

## Код

### Backend (Python)
- Python 3.12+
- FastAPI + Pydantic v2
- SQLAlchemy 2.x async + Alembic
- Форматтер: ruff
- Линтер: ruff + mypy
- Тесты: pytest + httpx

### Frontend (React, v2)
- React 18+ + TypeScript + Vite
- TailwindCSS + shadcn/ui
- Линтер: ESLint + Prettier

## Память

После каждой задачи обновить:
- `.ai_memory/tasks/<date>-<task-id>.md` — task summary
- `.ai_memory/projects/<slug>/agent-notes.md` — заметки
- `.ai_memory/current_state.md` — статус
- `PROJECT_MEMORY.md` — сводка (при необходимости)

## Запрещено

- Force push в `main`/`develop`
- Прямой merge в `main` без approve
- Коммитить `.env`, секреты, токены
- `rm -rf` вне рабочей папки
- Изменять `.opencode/agents/` без approve
- Создавать `memory/` в корне проекта
