# Project Memory Template

> Используется `MemoryProvisioningService` для создания файлов нового проекта.
> Плейсхолдеры вида `{{SLUG}}`, `{{NAME}}` заменяются при provisioning.

---

## Структура файлов (7 файлов)

При вызове `provision_project(slug, name)` создаются:

| Файл | Назначение |
|------|-----------|
| `overview.md` | Описание проекта, стек, repo, owner |
| `current_state.md` | Активный статус проекта |
| `architecture.md` | Архитектура, модули, границы |
| `decisions.md` | Архитектурные решения (ADR) |
| `tasks.md` | Текущие и завершённые задачи |
| `known_issues.md` | Известные проблемы и риски |
| `agent_notes.md` | Заметки агентов после задач |

---

## overview.md

```markdown
# Project: {{NAME}}

## Summary
[UNKNOWN — краткое описание проекта]

## Slug
{{SLUG}}

## Owner
[UNKNOWN]

## Repository
[UNKNOWN — путь к git-репозиторию]

## Production
- domain: [UNKNOWN]
- server: [UNKNOWN]
- deploy method: [UNKNOWN]

## Staging
- domain: [UNKNOWN]
- server: [UNKNOWN]
- deploy method: [UNKNOWN]

## Stack
- Language: [UNKNOWN]
- Framework: [UNKNOWN]
- Database: [UNKNOWN]
- Queue: [UNKNOWN]
- Frontend: [UNKNOWN]

## Important Commands
См. AGENTS.md в корне репозитория проекта.

## Deployment
См. AGENTS.md или deployment документацию проекта.

## Current Priorities
- [UNKNOWN]

## Known Risks
- [UNKNOWN]

## Agent Rules
- Перед изменениями создать отдельную ветку.
- Перед деплоем запускать тесты.
- Production deploy только после approve.
- Не писать secrets/tokens/passwords в память.
```

---

## current_state.md

```markdown
# {{NAME}} — Текущий статус

Обновлено: {{DATE}} | Автор: system

---

## Статус проекта

**Фаза:** [UNKNOWN]
**Состояние:** Проект зарегистрирован в Agent Mission Control.
**Блокеры:** Нет
**Критические проблемы:** Нет

## Что происходит сейчас

- Проект создан через Memory Provisioning Service.
- Память инициализирована шаблонами.

## Следующие шаги

1. Заполнить overview.md реальными данными.
2. Добавить архитектуру в architecture.md.
3. Создать AGENTS.md в корне репозитория проекта.

## Memory vault статус

| Компонент | Статус |
|-----------|--------|
| overview.md | ✅ Создан (template) |
| current_state.md | ✅ Создан (template) |
| architecture.md | ✅ Создан (template) |
| decisions.md | ✅ Создан (template) |
| tasks.md | ✅ Создан (template) |
| known_issues.md | ✅ Создан (template) |
| agent_notes.md | ✅ Создан (template) |
```

---

## architecture.md

```markdown
# {{NAME}} — Архитектура

## Обзор
[UNKNOWN — общее описание архитектуры]

## Структура директорий
[UNKNOWN]

## Основные модули
[UNKNOWN]

## API Contracts
[UNKNOWN]

## Data Flow
[UNKNOWN]

## Внешние зависимости
[UNKNOWN]

## Инфраструктура
[UNKNOWN]
```

---

## decisions.md

```markdown
# {{NAME}} — Архитектурные решения

## Как добавлять ADR

Для каждого значимого архитектурного решения создавайте новую секцию:

\```markdown
## ADR-XXXX: Название решения

**Дата:** YYYY-MM-DD
**Статус:** proposed | accepted | deprecated | superseded

### Контекст
Почему нужно принять решение.

### Решение
Что решили.

### Альтернативы
Что рассматривали.

### Последствия
Что изменится.
\```

---

*Пока нет архитектурных решений для этого проекта.*
```

---

## tasks.md

```markdown
# {{NAME}} — Задачи

## Активные задачи

| ID | Заголовок | Агент | Статус | Дата |
|----|-----------|-------|--------|------|
| — | — | — | — | — |

## Завершённые задачи

| ID | Заголовок | Агент | Результат | Дата |
|----|-----------|-------|-----------|------|
| — | — | — | — | — |

---

*Задачи добавляются автоматически через Agent Mission Control pipeline.*
```

---

## known_issues.md

```markdown
# {{NAME}} — Известные проблемы

## Открытые проблемы

| ID | Описание | Серьёзность | Статус |
|----|----------|-------------|--------|
| — | — | — | — |

## Решённые проблемы

| ID | Описание | Решение | Дата |
|----|----------|---------|------|
| — | — | — | — |

---

*Проблемы добавляются агентами после инцидентов и отладки.*
```

---

## agent_notes.md

```markdown
# {{NAME}} — Заметки агентов

## Правила

- Каждый агент добавляет заметки после завершения задачи.
- Формат: `## YYYY-MM-DD / agent-name / task-id`
- Писать кратко: что сделано, что важно для будущих задач.

---

*Пока нет заметок от агентов.*
```
