# .ai_memory/ — Obsidian-like Vault

> **Source of truth** для Agent Mission Control.
> Подключён к MCP через `opencode.json`.
> **Единственная система памяти проекта.** Корневая `memory/` не создаётся.

---

## Правила vault

### 1. Формат
Все файлы — Markdown с frontmatter (опционально) и человекочитаемым текстом.

### 2. Доступ на чтение
Любой агент может читать любой файл vault.

### 3. Доступ на запись

| Уровень | Файлы | Разрешено |
|---------|-------|-----------|
| **Free** | `tasks/*.md`, `projects/*/agent_notes.md`, `projects/*/tasks.md`, `projects/*/current_state.md` | Без approve |
| **Approval** | `projects/*/overview.md`, `projects/*/architecture.md`, `projects/*/decisions.md`, `decisions/*`, `current_state.md` | Через approve |
| **Forbidden** | secrets, tokens, passwords, credentials, private keys | Никогда |

### 4. Триггеры обновления
- После каждой задачи агент обновляет: `tasks/` (task summary), `projects/*/agent_notes.md`, `projects/*/current_state.md`.
- После архитектурного решения: `decisions/` (ADR), `projects/*/decisions.md`.
- После инцидента: `projects/*/known_issues.md`.

### 5. Запрет secrets
**Категорически запрещено** записывать в vault:
- API tokens / keys
- Passwords
- Private keys / certificates
- Session cookies
- Database credentials
- Любые credentials

Если в данных есть секрет, агент должен заменить его на `[REDACTED]` и добавить заметку.

### 6. Маркеры неизвестного
Использовать `[UNKNOWN]` для плейсхолдеров. Агенты заполняют при первом контакте с проектом.

### 7. Консистентность
- `_INDEX.md` обновляется при изменении структуры vault.
- `current_state.md` обновляется после каждой задачи.
- Версии файлов не дублируются — правится текущая версия.

---

## Структура vault

```text
.ai_memory/
├── README.md                           ← Этот файл (правила)
├── _INDEX.md                           ← Навигация
├── current_state.md                    ← Глобальный статус
├── agent_mission_control_pipeline.md   ← Пайплайн реализации
├── Добро пожаловать.md                 ← Не удалять!
│
├── projects/
│   ├── README.md                       ← Описание структуры
│   └── <project-slug>/                 ← Папка проекта (7 файлов)
│       ├── overview.md
│       ├── current_state.md
│       ├── architecture.md
│       ├── decisions.md
│       ├── tasks.md
│       ├── known_issues.md
│       └── agent_notes.md
│
├── agents/
│   ├── README.md                       ← Профили агентов
│   └── <agent-slug>.md                 ← Заметки/профиль агента
│
├── tasks/
│   ├── README.md                       ← Индекс логов задач
│   └── YYYY-MM-DD-task-<slug>.md       ← Task summaries
│
├── decisions/
│   ├── README.md                       ← Индекс ADR
│   └── 00XX-<slug>.md                  ← Architecture Decision Records
│
├── templates/
│   ├── project-memory-template.md      ← Шаблон project memory (7 файлов)
│   ├── task-summary-template.md        ← Шаблон task summary
│   ├── agent-notes-template.md         ← Шаблон agent notes
│   ├── adr-template.md                 ← Шаблон ADR
│   └── current-state-template.md       ← Шаблон current_state
│
└── .obsidian/                          ← Obsidian config
```

---

## Provisioning нового проекта

Через `MemoryProvisioningService.provision_project(slug, name)`:

1. Создаёт `.ai_memory/projects/<slug>/` (7 файлов из шаблонов).
2. Заменяет плейсхолдеры `{{SLUG}}`, `{{NAME}}`, `{{DATE}}`.
3. Не перезаписывает существующие файлы.
4. Возвращает список созданных/пропущенных файлов.
5. Обновляет `_INDEX.md`.
