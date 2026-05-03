# Роли агентов — Agent Mission Control

Версия: 1.0
Дата: 2026-05-03

## Обзор

Система использует специализированных агентов, каждый из которых отвечает за свою область. Агенты координируются через studio-orchestrator.

## Агенты

### 1. studio-orchestrator

**Роль:** Главный координатор проекта
**Отвечает за:** планирование, распределение задач, контроль порядка работ, approval-flow

**Ответственности:**
- Декомпозиция задач на backend/frontend/devops/memory/git задачи
- Создание планов и roadmap
- Определение, какой агент за что отвечает
- Определение безопасного порядка выполнения
- Запрос approve перед опасными действиями

**Файловые пути:** `docs/**`, `PROJECT_MEMORY.md`

### 2. knowledge-steward

**Роль:** Память проекта
**Отвечает за:** Obsidian-like markdown vault в `.ai_memory/`, PROJECT_MEMORY.md, ADR, индексы

**Файловые пути:** `.ai_memory/**/*.md`, `PROJECT_MEMORY.md`

### 3. software-architect

**Роль:** Архитектура системы
**Отвечает за:** сервисные границы, API contracts, event flow

**Файловые пути:** `docs/architecture.md`, `docs/database-schema.md`

### 4. backend-architect

**Роль:** Backend проекта
**Отвечает за:** FastAPI, aiogram Telegram bot, PostgreSQL, Redis, workers, API, task queue, интеграции с OpenCode

**Файловые пути:** `apps/api/**`, `apps/telegram-bot/**`, `apps/worker/**`

### 5. frontend-developer

**Роль:** Frontend проекта
**Отвечает за:** React dashboard, agents/tasks/projects/approvals UI

**Файловые пути:** `apps/web/**`

### 6. devops-automator

**Роль:** Инфраструктура проекта
**Отвечает за:** Docker, VPS, sandbox, deploy pipeline, logs, rollback

**Файловые пути:** `infra/**`, `Dockerfile`, `docker-compose*.yml`

### 7. git-workflow-master

**Роль:** Git workflow
**Отвечает за:** ветки, commits, PR, diff review, changelog

**Файловые пути:** Git-related, `CHANGELOG.md`

### 8. security-engineer

**Роль:** Безопасность проекта
**Отвечает за:** permissions, approvals, secrets, sandbox isolation, audit log

**Файловые пути:** `docs/security-policy.md`, `apps/api/app/security/**`

### 9. reality-checker

**Роль:** Проверка реальности
**Отвечает за:** QA, тесты, consistency review, smoke tests

**Файловые пути:** Test files, review reports

## Маршрутизация задач по агентам

| Тип задачи | Агент |
|------------|-------|
| FastAPI endpoint | backend-architect |
| Telegram bot handler | backend-architect |
| SQLAlchemy model | backend-architect |
| Celery task | backend-architect |
| Memory indexer | backend-architect |
| React component | frontend-developer |
| Dashboard page | frontend-developer |
| Docker Compose | devops-automator |
| Dockerfile | devops-automator |
| Sandbox setup | devops-automator |
| Nginx config | devops-automator |
| Memory vault update | knowledge-steward |
| ADR write | knowledge-steward |
| Security review | security-engineer |
| Audit log | security-engineer |
| Git branch strategy | git-workflow-master |
| PR creation | git-workflow-master |
| Code review | reality-checker |
| Architecture design | software-architect |
| Task planning | studio-orchestrator |
