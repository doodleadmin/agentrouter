# Task Summary — BE-07+ OpenCode 1.14.33 Native Contract Alignment

- **Date:** 2026-05-04
- **Agent:** backend-architect (implementation), knowledge-steward (recording)
- **Task ID:** BE-07+
- **Risk level:** medium

## Goal

Align OpenCode message payload and response mapping with the actual OpenCode 1.14.33 native contract. BE-07 used a simplified `{"message": "..."}` payload; BE-07+ adopts the proper `{"parts": [...]}` format with OpenCode-native part-type handling.

## Changed files

- `apps/api/app/integrations/opencode/schemas.py` — `OpenCodeSessionMessageRequest` now uses `parts: list[OpenCodeSessionTextPart]` instead of `message: str`
- `apps/api/app/integrations/opencode/client.py` — Request sends `{"parts": [{"type": "text", "text": "..."}]}` instead of `{"message": "..."}`; `_map_message_response_to_events` rewritten to handle OpenCode-native part types
- `apps/api/tests/test_opencode_transport.py` — new BE-07+ tests
- `apps/api/tests/test_runtime_be04.py` — updated for new contract
- `docs/smoke-test-opencode.md` — updated to reflect actual payload contract

## Key changes

### 1. Schema: `parts` instead of `message`

`OpenCodeSessionMessageRequest` now uses OpenCode-native structure:

```python
class OpenCodeSessionTextPart(BaseModel):
    type: Literal["text"]
    text: str

class OpenCodeSessionMessageRequest(BaseModel):
    parts: list[OpenCodeSessionTextPart]
```

### 2. Client: native part-type response mapping

`_map_message_response_to_events` rewritten with explicit OpenCode part-type dispatch:

| OpenCode part type | Event emitted | Notes |
|---|---|---|
| `text` | `plan.delta` | Plan text accumulation |
| `reasoning` | **SKIPPED** | Never stored in `plan_text` or events |
| `step-start` | skipped | Internal phase markers |
| `step-finish` (reason=stop) | `plan.final` | Plan completion signal |
| `tool` | `tool.call` | Tool invocation |
| unknown | `runtime_event_malformed` | Fail-closed |

### 3. Guardrails confirmed (unchanged)

- Default provider = `stub`
- `opencode_http` requires URL + `RUNTIME_ALLOW_REAL_OPENCODE_HTTP=True`
- No silent fallback
- Plan-only preserved
- Reasoning text NEVER stored in `plan_text`/events
- Redaction preserved at upper layers
- Real OpenCode NOT started during implementation

## Reviews

- **Security:** GO ✅ — all 8 checks PASS, no blocking issues
- **Architecture:** GO ✅ — all 5 rules PASS, no layering violations

## Validation

- `python -m compileall app` ✅
- `ruff check app` ✅
- `pytest tests -v` ✅ (`219 passed` — 12 new BE-07+ tests)

## Result

BE-07+ brings the message protocol to full OpenCode 1.14.33 contract compatibility. The simplified `{"message": "..."}` payload from BE-07 is replaced with the proper `{"parts": [{"type": "text", "text": "..."}]}` format. Response handling uses explicit OpenCode-native part-type dispatch with fail-closed behavior for unknown types.

## Open questions

- None.

## Follow-up tasks

- Optional: run controlled real-server smoke verification of BE-07+ contract (`POST /session/{id}/message` with `parts` payload) in local-only mode
