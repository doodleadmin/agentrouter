# BE-05 Hardening (B-1 + M-1/M-2/M-3)

**Дата:** 2026-05-04
**Агент:** backend-architect (implementation), security-engineer (audit)
**Статус:** ✅ Выполнена

---

## Контекст

BE-05 Phase 1 implementation завершила RealOpenCodeHttpTransport + 3 gap closures. Security review выявил 1 blocking finding + 3 medium findings, требующие исправления.

## Что исправлено

### B-1 (blocking): test_no_silent_fallback_to_stub_for_opencode_http
- Тест обновлён под новую семантику factory
- Проверяет: no silent fallback на stub, no stub fingerprint ("plan-only"/"No code execution"), runtime_error→task_failed path, provider remains opencode_http

### M-1: _truncate_plan session_id
- `session_id` parameter теперь используется в truncation marker: `[TRUNCATED — plan exceeded max size] (session=<id>)`
- Параметр больше не unused

### M-2: SSE non-JSON chunk limit (64KB)
- `_SSE_CHUNK_SIZE_LIMIT = 64 * 1024` в `RealOpenCodeHttpTransport`
- Non-JSON SSE чанки свыше лимита safely усекаются с `_sse_chunk_truncated=True` metadata
- Клиент эмитит `runtime_event_truncated` при обнаружении флага
- JSON SSE chunks НЕ ограничиваются

### M-3: RUNTIME_ALLOW_REAL_OPENCODE_HTTP safety gate
- `RUNTIME_ALLOW_REAL_OPENCODE_HTTP: bool = False` в config.py (default: disallow)
- Factory для `opencode_http` теперь требует ОБА условия: URL задан И allow flag=True
- Иначе → `RuntimeConfigurationError` (fail-closed)
- Fake/mocked transport разрешён только через explicit DI injection

## Изменённые файлы

| Файл | Изменение |
|------|-----------|
| `apps/api/app/config.py` | +`RUNTIME_ALLOW_REAL_OPENCODE_HTTP: bool = False` |
| `apps/api/app/integrations/opencode/factory.py` | Gate check для allow flag |
| `apps/api/app/integrations/opencode/transport.py` | SSE chunk size limit (64KB) |
| `apps/api/app/integrations/opencode/client.py` | session_id в truncation marker, SSE chunk truncation event |
| `apps/api/tests/test_runtime_be04.py` | B-1 test updated, +4 new M-3 tests, SSE chunk test |
| `apps/api/tests/test_opencode_transport.py` | +4 SSE chunk size tests |

## Тесты

- **compileall:** ✅
- **ruff:** ✅
- **pytest:** 205/205 passed (55 in BE-05 files)

## Обязательные тесты (все пройдены)

1. ✅ default provider remains stub
2. ✅ opencode_http без URL fail-closed
3. ✅ opencode_http без RUNTIME_ALLOW_REAL_OPENCODE_HTTP fail-closed
4. ✅ opencode_http с allow flag + недоступный сервер → runtime_error/task_failed
5. ✅ no silent fallback to stub
6. ✅ SSE non-JSON chunk > 64KB truncates safely
7. ✅ _truncate_plan session_id в truncation marker
8. ✅ real OpenCode server не запускался

## Ограничения соблюдены

- Реальный OpenCode server не запускался
- Default provider = stub подтверждён
- Все тесты через fake/mocked HTTP/SSE
- Без deploy/migrations/secrets/env/git
