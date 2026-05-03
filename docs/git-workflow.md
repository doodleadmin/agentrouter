# Git Workflow — Стратегия ветвления и работы с git

Версия: 1.0
Дата: 2026-05-03

## Branching Strategy

```
main ────────────────────────────── production
  │
  ├── develop ───────────────────── staging / integration
  │     │
  │     ├── agent/task-0001 ────── feature branch (worktree)
  │     ├── agent/task-0002
  │     └── ...
  │
  └── hotfix/* ──────────────────── экстренные исправления
```

## Основные правила

### 1. Никогда не работать в main
Все изменения — в отдельных ветках `agent/<task-id>`.

### 2. Одна задача — одна ветка
- Ветка живёт пока задача активна
- После merge — удалить (локально и remote)

### 3. Git Worktree для изоляции
На сервере каждая задача получает отдельный worktree:
```bash
git fetch --all
git checkout main
git pull
git worktree add /opt/mc/worktrees/<task-id> -b agent/<task-id>
```

После завершения:
```bash
git add .
git commit -m "agent: <описание>"
git push origin agent/<task-id>
```

### 4. Commit Message Convention
```
agent: <глагол в прошедшем времени> <что сделано>

Примеры:
agent: added /health endpoint and test
agent: created SQLAlchemy models for 8 tables
agent: fixed task status transition bug
agent: updated memory vault rules
```

### 5. Pull Request Flow
```
agent/task-0001
    ↓ git push
    ↓ create PR → develop (или main)
    ↓ CI: tests + lint
    ↓ review / approve
    ↓ merge
    ↓ delete branch
```

### 6. Merge Strategy
- `develop` ← `agent/*`: squash merge (один коммит на задачу)
- `main` ← `develop`: merge commit (сохранить историю релизов)

### 7. Запрещённые операции
- `git push --force` в `main`/`develop`
- `git reset --hard` на shared ветках
- `git commit --amend` после push
- Прямой merge в `main` без PR + approve
- Работа без отдельной ветки
- `rm -rf .git`

## Changelog

При каждом merge в `main` — обновить `CHANGELOG.md`.

## Связанные файлы
- [CONTRIBUTING.md](../CONTRIBUTING.md) — правила для разработчиков
- [AGENTS.md](../AGENTS.md) — правила для агентов
- [deployment-policy.md](deployment-policy.md) — политика деплоя
