---
type: task
task_id: BE-06-transport-compat
status: completed
risk: medium
requires_approval: false
date: '2026-05-04'
agent: studio-orchestrator
---

# BE-06: RealOpenCodeHttpTransport compatibility fix

## Scope
- Align runtime transport with current OpenCode server API contract for plan-only smoke readiness.
- No real OpenCode server execution.

## What changed
- Transport contract migrated from legacy:
  - `POST /sessions` + `GET /sessions/{id}/events`
- To current sync MVP contract:
  - `POST /session`
  - `POST /session/{id}/message`

## Implementation notes
- `apps/api/app/integrations/opencode/transport.py`
  - `create_session()` now uses `POST /session`
  - `send_message()` added for sync `POST /session/{id}/message`
  - malformed message payload fails closed
  - blocking security fix applied: bounded default `read_timeout` (uses `RUNTIME_SESSION_TIMEOUT_SECONDS` when unset)

- `apps/api/app/integrations/opencode/client.py`
  - switched runtime flow to sync message response
  - added mapper `parts -> {plan.delta, plan.final, tool.call}`
  - unknown/malformed parts fail closed (`runtime_error` / `runtime_event_malformed`)
  - plan-only guardrails preserved (policy_blocked, path confinement, truncation, retries)

- Tests updated:
  - `apps/api/tests/test_opencode_transport.py`
  - `apps/api/tests/test_runtime_be04.py`

- Docs aligned:
  - `docs/smoke-test-opencode.md` updated to endpoint probes using `/session` and `/session/{id}/message`

## Security review
- Initial review: CONDITIONAL (timeout hang risk)
- After fix: PASSED, GO for merge

## Validation
- `python -m compileall app` ✅
- `ruff check app` ✅
- `pytest tests -v` ✅ (193 passed)

## Constraints respected
- Real OpenCode server was NOT started
- `.env` not modified
- No deploy/migrations
