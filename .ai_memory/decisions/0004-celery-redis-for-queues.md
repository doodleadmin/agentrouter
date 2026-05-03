# 0004: Celery + Redis для очередей задач

Дата: 2026-05-03
Статус: accepted
Автор: studio-orchestrator

---

## Контекст
Нужен механизм фоновой обработки: Telegram inbound, agent plan/execute, memory index, staging/production deploy, notifications.

## Решение
**Celery** как task queue framework + **Redis** как broker и result backend.

## Альтернативы

### Dramatiq
- Плюсы: Простой API, меньше boilerplate
- Минусы: Меньше ecosystem

### RQ
- Плюсы: Очень простой
- Минусы: Нет сложных workflows, priorities

### BullMQ (Node.js)
- Плюсы: Хорошая интеграция с NestJS
- Минусы: Другой language runtime

## Последствия

### Положительные
- Самое зрелое Python-решение
- Retries, dead-letter, chaining, groups
- Redis — быстрый broker + кеширование

### Отрицательные
- API сложнее чем RQ/Dramatiq
- Redis требует отдельный сервис

## Затронутые компоненты
- `apps/worker/` — Celery worker
- `apps/api/app/workers/` — task definitions
- Redis в docker-compose
