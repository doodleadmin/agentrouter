# Memory Checkpoint Runbook

> MEM-04 Phase 2: Soft enforcement. Обязательное правило для всех агентов.

---

## 1. Что такое memory checkpoint

Memory checkpoint — это обновление проектной памяти в `.ai_memory/` и `PROJECT_MEMORY.md` после завершения значимой задачи.

Правило: **задача не считается завершённой, пока memory checkpoint не сделан или пропуск явно не обоснован.**

---

## 2. Когда memory checkpoint обязателен

| Ситуация | Требуется |
|----------|-----------|
| Задача завершена (`completed`) | Да |
| Задача провалена с полезными выводами (`failed`) | Да |
| Задача отменена с полезными выводами (`cancelled`) | Да |
| Live smoke / валидация | Да |
| Bug fix | Да |
| Infra/config изменение | Да |
| Архитектурное/дизайн-решение | Да |

---

## 3. Когда memory checkpoint можно пропустить

| Ситуация | Причина пропуска |
|----------|------------------|
| Тривиальный typo (1-2 строки) | Trivial change, no memory impact |
| Исследовательская команда без результата | Exploratory, no outcome |
| Повторная неудачная попытка без новых данных | No new information |
| Пользователь явно попросил не обновлять | User request |

**Важно:** пропуск должен быть явно указан в closeout report с конкретной причиной.

---

## 4. Обязательные файлы

После каждой значимой задачи обновить:

| Файл | Что обновить |
|------|-------------|
| `PROJECT_MEMORY.md` | Добавить запись о выполненной задаче, обновить статус |
| `.ai_memory/current_state.md` | Обновить статус, таблицу активных задач, счётчик логов |
| `.ai_memory/_INDEX.md` | Добавить запись в task log table, обновить счётчики |
| `.ai_memory/tasks/<YYYY-MM-DD>-task-<slug>.md` | **Создать** новый task log по шаблону |

Опционально:

| Файл | Когда обновлять |
|------|----------------|
| `.ai_memory/projects/<slug>/agent_notes.md` | Если задача меняет код или поведение конкретного проекта |
| `.ai_memory/projects/<slug>/current_state.md` | Если статус проекта изменился |

---

## 5. Что должен содержать каждый файл

### PROJECT_MEMORY.md

Запись о задаче в формате:

```markdown
### <task-id> — <краткое описание>

- **Статус:** completed | failed | cancelled
- **Дата:** <YYYY-MM-DD>
- **Изменённые файлы:** <список>
- **Commit:** <hash или N/A>
- **Валидация:** <результаты тестов>
- **Task log:** [.ai_memory/tasks/...](.ai_memory/tasks/...)
```

### .ai_memory/current_state.md

Обновить:

- `## Status` — статус системы
- `## Active Tasks` — таблица задач (удалить завершённые, добавить новые)
- `## Task Log Count` — инкрементировать счётчик

### .ai_memory/_INDEX.md

Добавить строку в таблицу `## Task Logs`:

```markdown
| <YYYY-MM-DD> | <задача> | <статус> | [ссылка](tasks/...) |
```

Инкрементировать `**Total:** N` счётчик.

### Task log

Создать файл `tasks/<YYYY-MM-DD>-task-<slug>.md` по шаблону: [task-summary-template.md](../templates/task-summary-template.md).

Обязательно заполнить секцию `## Память обновлена`.

---

## 6. Closeout report

Каждый closeout report должен включать:

```markdown
## Memory checkpoint
- **Memory updated:** yes/no
- **Files updated:** список файлов
- **Commit hash:** <hash или N/A>
- **Skipped reason:** <причина, если no>
```

---

## 7. Проверка перед git checkpoint

Перед созданием git checkpoint убедиться:

- [ ] `PROJECT_MEMORY.md` изменён
- [ ] `.ai_memory/current_state.md` изменён
- [ ] `.ai_memory/_INDEX.md` изменён
- [ ] task log создан
- [ ] Нет `.env`, `.env.local`, `logs/`, `__pycache__` в stage
- [ ] Нет секретов в изменённых файлах

---

## 8. Enforcement

| Фаза | Механизм | Статус |
|------|----------|--------|
| **Phase 2** (сейчас) | Soft enforcement через AGENTS.md, runbook, template | ✅ Внедрено |
| **Phase 3** (будущее) | API gate: `memory_checkpoint_done` флаг в БД, блокирует `completed`/`failed` без checkpoint | Отложено |

---

## 9. Шаблон task log

См. [task-summary-template.md](../templates/task-summary-template.md).

---

## 10. FAQ

**Q: Я сделал memory checkpoint, но забыл упомянуть в closeout report. Это проблема?**
A: Да. Closeout report — это доказательство для координатора. Без него задача формально не завершена.

**Q: Нужно ли обновлять память для каждой фазы задачи (TG-05 Phase 1, 2, 3)?**
A: Для промежуточных фаз — опционально. Для финальной фазы — обязательно. Используйте здравый смысл.

**Q: Что делать, если я не уверен, нужен ли memory checkpoint?**
A: Если сомневаетесь — делайте. Лишний checkpoint не навредит, пропущенный — оставит пробел в истории.

**Q: Кто проверяет, что memory checkpoint сделан?**
A: В Phase 2 — studio-orchestrator при закрытии задачи. В Phase 3 — API автоматически.

---

> **Помните:** память проекта — это то, что позволяет агентам работать эффективно. Без неё каждый агент начинает с нуля.
