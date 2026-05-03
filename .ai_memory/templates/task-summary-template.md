# Шаблон: Summary выполненной задачи

**Инструкция:** После завершения (или провала) задачи создать файл `.ai_memory/tasks/<YYYY-MM-DD>-<task-id>.md`.

---

```markdown
# Task: <external_id>

Дата: <YYYY-MM-DD>
Агент: <agent_slug>
Проект: <project_slug>

---

## Постановка задачи
<Оригинальный текст>

## Риск-уровень
<low | medium | high | critical>

## План
1. ...
2. ...

## Статус
<completed | failed | cancelled>

---

## Изменённые файлы
- <путь> — new | modified | deleted

## Выполненные команды
- `<команда>` → passed / failed

## Результаты тестов
passed: <число>, failed: <число> / Не применялось

## Diff summary
<файл>: +<добавлено> -<удалено>

## PR
<ссылка или "Не создан">

---

## Риски, возникшие при выполнении
<Нет / ...>

## Уроки (Lessons Learned)
<Нет / ...>

## Следующие шаги
<Нет / ...>

---

## Память обновлена
- [ ] agent-notes.md
- [ ] tasks.md
- [ ] current_state.md
```
