# Task: BE-10 Runtime Reliability Hardening

Дата: 2026-05-04
Агент: backend-architect
Проект: agent-mission-control

---

## Постановка задачи
Hardening runtime reliability после BE-09 Phase 2 success: устранить timing/ordering/re-entry gaps, выявленные при real OpenCode smoke (retry на 180s boundary, notification на fail, event ordering).

## Риск-уровень
low (config tuning + defensive programming)

## План
1. P0-1: Idempotency guard for PLANNING state — guard BEFORE transition, blocks re-entry for PLANNING/APPROVED/WAITING_APPROVAL/COMPLETED
2. P0-2: trigger-plan status gate — only CREATED tasks accepted, 409 otherwise
3. P1-3: Notification isolation in worker — plan generation and notification dispatch in separate try blocks
4. P1-4: Retry exception handling in OpenCodeHttpPlanClient — catches OpenCodeTimeoutError/OpenCodeConnectionError
5. P2-5: Event ordering — runtime_session_created emitted BEFORE retry loop (inside generate_plan after POST /session)
6. P2-6: Timeout alignment — RUNTIME_SESSION_TIMEOUT_SECONDS 180→300, API_TIMEOUT_SECONDS 300→420

## Статус
completed

---

## Изменённые файлы (10 code + memory)
- `apps/api/app/config.py` — RUNTIME_SESSION_TIMEOUT_SECONDS 180→300, API_TIMEOUT_SECONDS 300→420
- `apps/api/app/integrations/opencode/client.py` — catch OpenCodeTimeoutError/OpenCodeConnectionError in retry loop
- `apps/api/app/tasks.py` — trigger-plan 409 gate for non-CREATED tasks
- `apps/api/app/schemas/task.py` — exported constants for status gate
- `apps/api/app/services/runtime_service.py` — idempotency guard (PLANNING/APPROVED/WAITING_APPROVAL/COMPLETED), event ordering (session_created before retry)
- `apps/api/tests/test_runtime_be04.py` — +9 new BE-10 tests (idempotency, status gate, timeout config)
- `apps/worker/app/config.py` — API_TIMEOUT_SECONDS 300→420
- `apps/worker/app/tasks/agent_plan.py` — notification isolation (separate try blocks for plan generation + notification dispatch)
- `apps/worker/tests/test_agent_plan_pipeline.py` — +2 new BE-10 tests (notification isolation)
- `apps/worker/tests/test_config.py` — +1 new BE-10 config test (timeout alignment)

## Выполненные команды
- `python -m compileall apps/api/app && python -m compileall apps/worker/app` → passed
- `ruff check apps/api/app apps/worker/app` → passed
- `pytest apps/api/tests -v` → 237/237 passed (71 in test_runtime_be04.py, 9 new BE-10)
- `pytest apps/worker/tests -v` → 93/93 passed (3 new BE-10)

## Результаты тестов
- API: 237/237 passed
- Worker: 93/93 passed
- Security review: PASS (6/6)
- Architecture review: PASS (5/5)
- Reality-check: PASS (6/6)

## Diff summary
- `config.py` (API): 2 timeout constants changed
- `config.py` (Worker): 1 timeout constant changed
- `client.py`: retry exception handling expanded
- `tasks.py` (API): status gate + 409 response
- `runtime_service.py`: idempotency guard + event ordering fix
- `agent_plan.py` (Worker): notification isolation
- `test_runtime_be04.py`: +9 tests
- `test_agent_plan_pipeline.py`: +2 tests
- `test_config.py` (Worker): +1 test

## PR
Не создан

---

## Риски, возникшие при выполнении
Нет

## Уроки (Lessons Learned)
- Real OpenCode plans могут занимать 80–170s; worker API timeout должен быть >= session timeout + buffer
- retry boundary (180s) был borderline — увеличение до 300s исключает false retries
- session_created до retry loop критично для traceability: позволяет идентифицировать сессию даже при таймауте

## Следующие шаги
- Memory retrieval tuning (ranking quality + scope heuristics)
- Следующий major milestone: Phase 1 (Telegram routing) — уже реализовано; Phase 2 (Project memory) — уже реализовано; движемся к Phase 3/4 hardening

---

## Память обновлена
- [x] current_state.md
- [x] _INDEX.md
- [x] PROJECT_MEMORY.md

## Notes
- Real OpenCode was NOT started during implementation
- Provider default remains `stub`
- `RUNTIME_ALLOW_REAL_OPENCODE_HTTP` remains `False`
- `.env`/secrets untouched
- No guardrails weakened (plan-only, fail-closed, path confinement, redaction — all preserved)
- All three reviews PASSED (Security 6/6, Architecture 5/5, Reality-check 6/6)
