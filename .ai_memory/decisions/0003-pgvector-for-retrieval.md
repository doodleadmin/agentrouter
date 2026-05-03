# 0003: pgvector для семантического retrieval

Дата: 2026-05-03
Статус: accepted
Автор: studio-orchestrator

---

## Контекст
Система памяти нуждается в семантическом поиске по markdown vault.

## Решение
Использовать **pgvector** — PostgreSQL extension. Хранить embeddings в `memory_chunks` с типом `VECTOR(1536)`.

## Альтернативы

### Qdrant
- Плюсы: Лучшая производительность на больших данных
- Минусы: Дополнительный сервис, сложнее MVP

### ChromaDB
- Плюсы: Простая установка, Python-native
- Минусы: Не production-ready для distributed

## Последствия

### Положительные
- Нет дополнительного сервиса
- SQL-запросы для векторного поиска
- Простой переход на Qdrant через абстракцию

### Отрицательные
- Медленнее Qdrant > 1M векторов
- IVFFlat index требует periodic rebuild

## Migration path
1. Абстракция retriever interface на месте
2. Переключиться на Qdrant при необходимости
