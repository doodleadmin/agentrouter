# BE-05 Phase 1 Hardening — B-1 + M-1/M-2/M-3 Security Findings Fixed

**Дата:** 2026-05-04
**Агент:** backend-architect
**Статус:** ✅ Выполнена
**Контур:** local only; без deploy/migrations/secrets/OpenCode.

## Findings закрыты

### B-1 (blocking): test_no_silent_fallback_to_stub_for_opencode_http
- **Проблема:** Тест не покрывал новую семантику factory (RealOpenCodeHttpTransport вместо RuntimeConfigurationError до network).
- **Фикс:** Тест обновлён. Проверяет: нет silent fallback, нет stub fingerprint ("plan-only"/"No code execution"), ошибка через runtime_error→task_failed, provider остаётся opencode_http.
- С добавлением M-3 gate, тест теперь покрывает fail-closed на уровне factory (RuntimeConfigurationError от gate).

### M-1: _truncate_plan session_id
- **Проблема:** Параметр session_id был неиспользуемым.
- **Фикс:** session_id включён в truncation marker: `[TRUNCATED — plan exceeded max size] (session=<id>)`.

### M-2: SSE non-JSON chunk limit
- **Проблема:** Non-JSON SSE data оборачивалась без размера лимита.
- **Фикс:** Per-chunk limit 64KB в `_parse_sse_event()`. При превышении — safe truncation + metadata `_sse_chunk_truncated=True`. Клиент эмитит `runtime_event_truncated` с reason. JSON SSE chunks не ограничиваются.

### M-3: RUNTIME_SAFE_MODE gate
- **Проблема:** Реальный transport мог быть создан без explicit opt-in.
- **Фикс:** Добавлен `RUNTIME_ALLOW_REAL_OPENCODE_HTTP: bool = False` (default) в config. Factory для opencode_http требует ОБА условия: URL задан И allow flag=True. Иначе → `RuntimeConfigurationError` (fail-closed).

## Изменённые файлы

1. `apps/api/app/config.py` — добавлен RUNTIME_ALLOW_REAL_OPENCODE_HTTP
2. `apps/api/app/integrations/opencode/factory.py` — gate check
3. `apps/api/app/integrations/opencode/transport.py` — SSE chunk size limit
4. `apps/api/app/integrations/opencode/client.py` — session_id в truncation marker, SSE chunk truncation event
5. `apps/api/tests/test_runtime_be04.py` — B-1 updated, 4 new tests
6. `apps/api/tests/test_opencode_transport.py` — 4 new SSE chunk tests

## Тесты (8 required scenarios)

1. ✅ default provider remains stub
2. ✅ opencode_http без URL fail-closed
3. ✅ opencode_http без RUNTIME_ALLOW_REAL_OPENCODE_HTTP fail-closed (NEW)
4. ✅ opencode_http с allow flag + недоступный сервер → runtime_error/task_failed (NEW)
5. ✅ no silent fallback to stub (UPDATED B-1)
6. ✅ SSE non-JSON chunk > 64KB truncates safely (NEW × 4)
7. ✅ _truncate_plan session_id в truncation marker (UPDATED)
8. ✅ real OpenCode server не запускался (NEW)

## Проверки

- `python -m compileall app` ✅
- `ruff check app` ✅
- `pytest tests -v` ✅ (205/205)

## Ограничения

- Реальный OpenCode server не запускался
- Default provider = stub подтверждён
- Без deploy/migrations/secrets
