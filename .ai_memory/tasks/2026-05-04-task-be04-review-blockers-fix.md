# Task Summary — BE-04 review blockers fix

Date: 2026-05-04
Agent: backend-architect
Scope: apps/api runtime plan-only path

## What was fixed

1. Redaction leak fixed with value-level masking:
   - key/value secrets,
   - bearer tokens,
   - private key blocks,
   - env-like secret assignments.
2. Layering corrected:
   - guardrails moved to `app/policy/runtime_guardrails.py`.
3. Provider abstraction corrected:
   - runtime wiring via factory/DI (`integrations/opencode/factory.py`),
   - service no longer hard-wires FakeOpenCode transport.
4. Observability extended:
   - emits `runtime_event_received`, `runtime_duplicate_event_ignored`, `runtime_retry_scheduled`.
5. Root confinement consistency:
   - project paths validated before provider execution (including stub mode).

## Validation

- `python -m compileall app` ✅
- `ruff check app` ✅
- `pytest tests -v` ✅ (162 passed)

## Safety

- Real OpenCode runtime/server not started.
- Only fake/mocked HTTP/SSE behavior used in tests.
- No deploy/migrations/.env/secrets changes.
