# 0002: Python Backend — FastAPI + aiogram + Celery + SQLAlchemy

Дата: 2026-05-03
Статус: accepted
Автор: studio-orchestrator

---

## Контекст
Нужно выбрать основной технологический стек для backend-части системы.

## Решение
Python 3.12+ со стеком: FastAPI, aiogram 3.x, Celery + Redis, SQLAlchemy 2.x async, Pydantic v2.

## Альтернативы

### Node.js / NestJS
- Плюсы: Единый язык с React, async нативно
- Минусы: Другой ecosystem для AI agent integration

### Django + DRF
- Плюсы: Зрелый, ORM встроен, admin
- Минусы: Синхронный, тяжёлый для microservice

## Последствия

### Положительные
- Async нативно (FastAPI + aiogram + SQLAlchemy async)
- Единый язык (Python) для всего backend
- Автогенерация OpenAPI-документации

### Отрицательные
- Python медленнее Go/Rust для CPU-bound
- GIL ограничивает parallelism

## Затронутые компоненты
- `apps/api/` — FastAPI
- `apps/telegram-bot/` — aiogram
- `apps/worker/` — Celery
