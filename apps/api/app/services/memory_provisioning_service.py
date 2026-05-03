"""Memory provisioning service — creates and manages project memory vaults.

Creates per-project folders inside `.ai_memory/projects/<slug>/` with 7 files:
overview.md, current_state.md, architecture.md, decisions.md,
tasks.md, known_issues.md, agent_notes.md.

Template functions are defined at module level and collected in PROJECT_FILES dict.
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from app.config import settings
from app.schemas.memory import (
    MemoryFileResult,
    MemoryProjectInfo,
    MemoryProvisionResult,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Template functions — each returns file content for a project memory file.
# Signature: (slug, name, date_str) -> str
# ---------------------------------------------------------------------------

def _overview_template(slug: str, name: str, _date: str) -> str:
    return f"""# Project: {name}

## Summary
[UNKNOWN — краткое описание проекта]

## Slug
{slug}

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
"""


def _current_state_template(slug: str, name: str, _date: str) -> str:
    return f"""# {name} — Текущий статус

Обновлено: {_date} | Автор: system

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
"""


def _architecture_template(slug: str, name: str, _date: str) -> str:
    return f"""# {name} — Архитектура

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
"""


def _decisions_template(slug: str, name: str, _date: str) -> str:
    return f"""# {name} — Архитектурные решения

## Как добавлять ADR

Для каждого значимого архитектурного решения создавайте новую секцию:

```markdown
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
```

---

*Пока нет архитектурных решений для этого проекта.*
"""


def _tasks_template(slug: str, name: str, _date: str) -> str:
    return """# Задачи

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
"""


def _known_issues_template(slug: str, name: str, _date: str) -> str:
    return """# Известные проблемы

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
"""


def _agent_notes_template(slug: str, name: str, _date: str) -> str:
    return f"""# {name} — Заметки агентов

## Правила

- Каждый агент добавляет заметки после завершения задачи.
- Формат: `## YYYY-MM-DD / agent-name / task-id`
- Писать кратко: что сделано, что важно для будущих задач.

---

*Пока нет заметок от агентов.*
"""


# ---------------------------------------------------------------------------
# File definitions: filename -> template function
# ---------------------------------------------------------------------------

PROJECT_FILES: dict[str, callable] = {
    "overview.md": _overview_template,
    "current_state.md": _current_state_template,
    "architecture.md": _architecture_template,
    "decisions.md": _decisions_template,
    "tasks.md": _tasks_template,
    "known_issues.md": _known_issues_template,
    "agent_notes.md": _agent_notes_template,
}


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class MemoryProvisioningService:
    """Creates and manages project memory vaults inside .ai_memory/projects/."""

    def __init__(self, vault_path: str | None = None) -> None:
        self._vault_path = Path(vault_path or settings.MEMORY_VAULT_PATH)
        self._projects_dir = self._vault_path / "projects"

    @property
    def vault_path(self) -> Path:
        return self._vault_path

    @property
    def projects_dir(self) -> Path:
        return self._projects_dir

    def provision_project(self, slug: str, name: str) -> MemoryProvisionResult:
        """Create memory folder for a project with 7 template files.

        Does NOT overwrite existing files.

        Args:
            slug: Project slug (lowercase, hyphens).
            name: Human-readable project name.

        Returns:
            MemoryProvisionResult with list of created/skipped files.
        """
        project_dir = self._projects_dir / slug
        project_dir.mkdir(parents=True, exist_ok=True)

        today = date.today().isoformat()
        file_results: list[MemoryFileResult] = []

        for filename, template_func in PROJECT_FILES.items():
            filepath = project_dir / filename
            if filepath.exists():
                file_results.append(
                    MemoryFileResult(
                        filename=filename,
                        status="skipped",
                        path=str(filepath),
                    )
                )
                continue

            content = template_func(slug, name, today)
            filepath.write_text(content, encoding="utf-8")
            file_results.append(
                MemoryFileResult(
                    filename=filename,
                    status="created",
                    path=str(filepath),
                )
            )

        logger.info(
            "provision_project: slug=%s created=%d skipped=%d",
            slug,
            sum(1 for f in file_results if f.status == "created"),
            sum(1 for f in file_results if f.status == "skipped"),
        )

        return MemoryProvisionResult(
            slug=slug,
            project_dir=str(project_dir),
            files=file_results,
        )

    def get_project_info(self, slug: str) -> MemoryProjectInfo:
        """Get info about a project's memory vault.

        Args:
            slug: Project slug.

        Returns:
            MemoryProjectInfo with file list and existence flag.
        """
        project_dir = self._projects_dir / slug
        exists = project_dir.is_dir()

        files: list[str] = []
        if exists:
            for f in sorted(project_dir.iterdir()):
                if f.is_file() and f.suffix == ".md":
                    files.append(f.name)

        return MemoryProjectInfo(
            slug=slug,
            project_dir=str(project_dir),
            files=files,
            exists=exists,
        )

    def list_projects(self) -> list[MemoryProjectInfo]:
        """List all projects with memory vaults.

        Returns:
            List of MemoryProjectInfo for each project.
        """
        if not self._projects_dir.is_dir():
            return []

        result: list[MemoryProjectInfo] = []
        for entry in sorted(self._projects_dir.iterdir()):
            if entry.is_dir() and not entry.name.startswith("."):
                result.append(self.get_project_info(entry.name))

        return result
