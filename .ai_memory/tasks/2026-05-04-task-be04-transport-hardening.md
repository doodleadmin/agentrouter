# Task Summary — BE-04 transport hardening

Date: 2026-05-04
Agent: backend-architect
Scope: `F:\dev\agentrouter` only

## Goal
Убрать hidden misconfiguration, где `opencode_http` мог получать fake transport по умолчанию, и перевести provider wiring в строгий fail-closed режим.

## What changed
- `RUNTIME_PROVIDER` оставлен с default `stub`.
- Добавлен обязательный `OPENCODE_SERVER_URL` для `opencode_http`.
- Factory больше не создаёт `FakeOpenCodeHttpClient` по умолчанию.
- `opencode_http` без URL/required config => `RuntimeConfigurationError` => `runtime_error` + `task_failed`.
- Unknown provider => fail-closed (`runtime_error` + `task_failed`).
- Fake transport разрешён только через explicit DI в тестах.

## Files
- `apps/api/app/config.py`
- `apps/api/app/integrations/opencode/factory.py`
- `apps/api/app/integrations/opencode/client.py`
- `apps/api/tests/test_runtime_be04.py`
- `apps/api/tests/test_runtime.py`
- `docs/security-policy.md`
- `PROJECT_MEMORY.md`
- `.ai_memory/current_state.md`
- `.ai_memory/_INDEX.md`

## Verification
- `python -m compileall app` ✅
- `ruff check app` ✅
- `pytest tests -v` ✅ (167 passed)

## Security invariants
- Plan-only boundary: preserved.
- Mutating tools policy_blocked: preserved.
- Root confinement: preserved.
- Memory minimization: preserved.
- Real OpenCode runtime/server: not started.
