# AGENTS.md — Правила для агентов в проекте Agent Mission Control

## Проект

Agent Mission Control — orchestration platform для управления AI-агентами через Telegram + OpenCode.

## Общие правила

1. **Сначала план, потом действие.** Любое изменение кода, инфраструктуры или данных должно начинаться с плана.
2. **Только в своей ветке.** Все изменения делаются в отдельной ветке `agent/<task-id>`. Никогда не работаем напрямую в `main` или `develop`.
3. **Тесты перед завершением.** Если задача меняет код, запустить тесты перед финальным ответом.
4. **Безопасность прежде всего.** Не трогать production secrets, не делать force push, не удалять миграции без подтверждения.
5. **Память обязательна.** После каждой задачи обновить `.ai_memory/` и `PROJECT_MEMORY.md`.
6. **Ясный формат ответа.** Каждый ответ агента должен содержать: plan, changed files, commands run, risks, next steps.

## Project Root

Единственная рабочая папка: **`F:\dev\agentrouter`**

Запрещено использовать `F:\dev\agent-mission-control` или любые другие директории как project root.

## Риск-уровни

| Уровень | Действия | Требует approve |
|---------|----------|-----------------|
| low | Чтение, анализ, план | Нет |
| medium | Изменение кода, запуск тестов, staging deploy | Да для deploy |
| high | Миграции, изменение env, restart сервисов | Да |
| critical | Production deploy, удаление данных, секреты | Да, обязательно |

## Запрещено

- Прямой merge в `main` без approval
- Доступ к production `.env` без подтверждения
- `rm -rf` вне рабочей директории
- Force push
- Удаление миграций без подтверждения
- Запуск кода вне Docker sandbox (кроме read-only операций)
- Создавать или менять `.env` / secrets / tokens
- Подключаться к реальным серверам и production DB без approve
- Запускать shell-команды без отдельного approve
- Делать deploy без отдельного approve
- Создавать `memory/` директорию в корне проекта

## Структура памяти

Память проекта организована в **`.ai_memory/`** — Obsidian-like vault, подключённый к MCP:

- `.ai_memory/decisions/` — архитектурные решения (ADR)
- `.ai_memory/templates/` — шаблоны документов
- `.ai_memory/projects/<slug>/` — память по каждому проекту
- `.ai_memory/agents/` — профили агентов
- `.ai_memory/tasks/` — логи задач

`PROJECT_MEMORY.md` — краткий индекс, ссылающийся на `.ai_memory/`.

Перед началом работы с проектом — прочитать его память через `.ai_memory/`.

## Агенты

| Агент | Роль |
|-------|------|
| backend-architect | FastAPI, aiogram, PostgreSQL, Redis, workers |
| frontend-developer | React, Vite, TailwindCSS, dashboard UI |
| devops-automator | Docker, VPS, deploy, logs, sandbox |
| knowledge-steward | Memory vault, заметки, ADR, индексы |
| security-engineer | Permissions, approvals, secrets, audit |
| git-workflow-master | Ветки, commits, PR, changelog |
| reality-checker | Тесты, consistency review, verification |
| software-architect | Архитектура, сервисные границы, API contracts |
| studio-orchestrator | Координация, планирование, распределение задач |

Подробнее: [docs/agent-roles.md](docs/agent-roles.md)

## Формат ответа агента

```markdown
## Plan
1. ...
2. ...

## Files likely to change
- ...

## Commands to run
- ...

## Risks
- ...

## Requires approval
yes/no
```

## Git workflow

```bash
# Создание ветки для задачи
git fetch --all
git checkout main
git pull
git worktree add /path/to/worktrees/<task-id> -b agent/<task-id>

# После завершения
git add .
git commit -m "agent: <краткое описание>"
git push origin agent/<task-id>
```

## После каждого изменения

Каждый агент обязан:
- показать список изменённых файлов
- кратко описать изменения
- обновить `PROJECT_MEMORY.md` или `.ai_memory/`
- остановиться и ждать следующего approve

## Команды проекта

> Будут добавлены после создания backend-кода.

## Deployment

Staging: автоматический после прохождения тестов.
Production: только через approval.

Политика деплоя: [docs/deployment-policy.md](docs/deployment-policy.md)
