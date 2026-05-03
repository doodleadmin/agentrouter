# Decisions — Архитектурные решения (ADR)

Индекс всех Architecture Decision Records.

---

## Принятые решения

| ADR | Название | Дата | Статус |
|-----|----------|------|--------|
| [0001](0001-use-monorepo.md) | Использовать Monorepo | 2026-05-03 | accepted |
| [0002](0002-python-backend-fastapi.md) | Python Backend — FastAPI + aiogram + Celery + SQLAlchemy | 2026-05-03 | accepted |
| [0003](0003-pgvector-for-retrieval.md) | pgvector для семантического retrieval | 2026-05-03 | accepted |
| [0004](0004-celery-redis-for-queues.md) | Celery + Redis для очередей задач | 2026-05-03 | accepted |

---

## Шаблон

При добавлении нового решения используйте шаблон: [templates/adr-template.md](../templates/adr-template.md)

## Правила

- Нумерация сквозная: 0001, 0002, 0003...
- Название файла: `<NNNN>-<title>.md` (строчные, через дефис)
- Статус: proposed → accepted → deprecated | superseded
- Глобальные решения — здесь, локальные решения проекта — в `projects/<slug>/decisions.md`
