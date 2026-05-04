# Task Summary — BE-07 Payload Contract Alignment Implementation

- **Date:** 2026-05-04
- **Agent:** knowledge-steward (recording backend-architect implementation)
- **Task ID:** BE-07

## Goal
Record completion of BE-07: align OpenCode message payload contract and runtime response handling for `/session/{id}/message`.

## Changed files
- `apps/api/app/integrations/opencode/client.py`
- `apps/api/app/integrations/opencode/transport.py`
- `apps/api/tests/**` (runtime transport/client coverage updates)

## Result
- Payload changed from legacy extra-fields shape to minimal `{ "message": <text> }` for `POST /session/{id}/message`.
- Client response mapping updated to accept both `parts` and `content` shapes.
- Fail-closed behavior enforced for empty, malformed, or unknown response structures.
- Guardrails preserved: plan-only mode, `policy_blocked` for mutating `tool.call`, path confinement, redaction at upper layers, `max_plan_size`, timeout, and no silent fallback.
- Architecture blocker fixed: removed policy-layer dependency from `transport.py`; transport remains transport-only.

## Validation
- `python -m compileall app` ✅
- `ruff check app` ✅
- `pytest tests -v` ✅ (`204 passed`)
- Real OpenCode server was **not** started during implementation/tests.

## Open questions
- None.

## Follow-up tasks
- Optional: run a controlled real-server smoke verification for BE-07 contract (`POST /session/{id}/message`) in local-only mode.
