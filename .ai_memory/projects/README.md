# projects/ — Память проектов

> Каждый проект имеет свою папку `.ai_memory/projects/<project-slug>/` с 7 файлами.

---

## Структура project memory

| Файл | Назначение | Доступ |
|------|-----------|--------|
| `overview.md` | Описание, стек, repo, owner | Approval |
| `current_state.md` | Активный статус проекта | Free |
| `architecture.md` | Архитектура, модули, границы | Approval |
| `decisions.md` | Архитектурные решения (ADR) | Approval |
| `tasks.md` | Текущие и завершённые задачи | Free |
| `known_issues.md` | Известные проблемы и риски | Free |
| `agent_notes.md` | Заметки агентов после задач | Free |

---

## Provisioning

При регистрации проекта через `MemoryProvisioningService`:

1. Создаётся папка `.ai_memory/projects/<slug>/`
2. 7 файлов генерируются из шаблона `templates/project-memory-template.md`
3. Плейсхолдеры `{{SLUG}}`, `{{NAME}}`, `{{DATE}}` заменяются
4. Существующие файлы **не перезаписываются**

---

## Зарегистрированные проекты

*Пока нет. Проекты появятся после вызова provisioning через API или Telegram.*
