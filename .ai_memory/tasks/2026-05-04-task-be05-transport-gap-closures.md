# BE-05: RealOpenCodeHttpTransport + gap closures — Implementation Phase 1

Date: 2026-05-04 | Agent: backend-architect | Status: ✅ Completed

## Summary

Implemented `RealOpenCodeHttpTransport` (HTTP/SSE via httpx) and closed 3 gaps:
- **max_plan_size** — 100KB hard cap with truncation + warning event
- **timeout enforcement** — session total + idle timeout in both transport and client
- **tool.call path confinement** — block escape/traversal/UNC/drive-mismatch for read/search paths

No real OpenCode server was started. All tests use mocked/fake HTTP/SSE. `RUNTIME_PROVIDER=stub` remains default.

## Changes

### 1. RealOpenCodeHttpTransport (NEW)
`apps/api/app/integrations/opencode/transport.py`
- Implements `OpenCodeTransportProtocol` (create_session + stream_events)
- Uses `httpx.AsyncClient` with configurable Timeout (connect/read/write)
- `create_session`: POST `/sessions`, returns session_id
- `stream_events`: GET `/sessions/{id}/events`, SSE parsing with event boundary detection
- Error handling: ConnectError → OpenCodeConnectionError, HTTPStatusError → OpenCodeHTTPError, ReadTimeout → OpenCodeTimeoutError
- URL redaction via `_redact_url()` + payload redaction
- Session total timeout + idle timeout enforced during SSE iteration

### 2. max_plan_size (config + client)
- `RUNTIME_MAX_PLAN_BYTES: int = 100_000` added to `config.py`
- `OpenCodeHttpPlanClient._truncate_plan()`: hard UTF-8 truncation with `[TRUNCATED]` marker
- Truncation emits `runtime_event_truncated` audit event

### 3. timeout enforcement (transport + client)
- Transport: session timeout + idle timeout during `stream_events()` iteration
- Client: same timeouts checked per SSE event, provider-agnostic
- Uses `RUNTIME_SESSION_TIMEOUT_SECONDS` (60s) and `RUNTIME_IDLE_TIMEOUT_SECONDS` (20s)
- Timeout → controlled `runtime_timeout` + `task_failed`

### 4. tool.call path confinement (client + policy)
- For `tool.call` events with action=read or action=search: path validated via `ensure_path_confined()`
- Blocks: traversal (`../`), absolute escape, symlink/junction, UNC/network paths, drive mismatch
- Violation → `policy_blocked` + `task_failed`

### 5. SSE robustness improvements
- `KNOWN_SSE_EVENT_TYPES = frozenset({"plan.delta", "plan.final", "tool.call"})`
- Missing `type` → `runtime_event_malformed`
- Unknown `type` → `runtime_error`
- Duplicate `event_id` → `runtime_duplicate_event_ignored`
- Non-JSON SSE data → wrapped as `plan.delta`

### 6. Redaction (no regression)
- Transport redacts payload before POST, error messages before exception raise
- Client redacts event text, plan_parts, and tool paths
- No redaction bypass from new transport layer

### 7. Factory update
- `factory.py`: when no `transport_factory` provided for `opencode_http`, defaults to `RealOpenCodeHttpTransport()` (production path)
- Explicit DI with fake transport still supported for tests

### 8. Documentation
- `docs/smoke-test-opencode.md` — future smoke test procedure with pre-conditions, steps, abort criteria, post-smoke checks

### 9. Tests
- `apps/api/tests/test_opencode_transport.py` (NEW, 19 tests):
  - T1-T4: create_session (success, fallback id, HTTP 500, missing session_id)
  - T3: connection error + read timeout
  - T5: stream_events (parsed events, multiline data, non-JSON, non-data lines, empty buffer)
  - T6-T7: session total timeout, idle timeout
  - T8: stream_events connection error, read timeout, HTTP error
  - Redaction: payload, error messages, URL params
- `apps/api/tests/test_runtime_be04.py` (updated, +12 new tests):
  - max_plan_size truncation + warning event
  - Small plan no truncation
  - Client session timeout → failed
  - Tool path allowed inside root
  - Tool path blocks escape, UNC paths, skips without path
  - SSE malformed missing type → event_malformed
  - SSE unknown event type → runtime_error
  - Redaction not bypassed by truncation
  - No silent fallback to stub preserved

## Verification
- `python -m compileall app` ✅
- `ruff check app` ✅
- `pytest tests -v` ✅ (197/197 passed)

## How 3 gaps are closed

| Gap | Mechanism | Layer |
|-----|-----------|-------|
| max_plan_size | `RUNTIME_MAX_PLAN_BYTES`, `_truncate_plan()`, `runtime_event_truncated` | client |
| timeout enforcement | Session/idle timeout in transport + client, `runtime_timeout` | transport, client |
| tool.call path | `ensure_path_confined()` in client for read/search actions, `policy_blocked` | client, policy |

## Architecture: RealOpenCodeHttpTransport

```
OpenCodeHttpPlanClient
    │
    ▼
RealOpenCodeHttpTransport (implements OpenCodeTransportProtocol)
    │  create_session(payload) → POST /sessions → str session_id
    │  stream_events(session_id) → GET SSE /sessions/{id}/events → AsyncIterator[dict]
    │
    ▼
httpx.AsyncClient
    │  Timeout(connect, read, write)
    │  Session total timeout check
    │  Idle timeout check
    │  Redaction before send / in errors
    ▼
OpenCode Server (not run in this task)
```

## Confirmations
- `default=stub`: ✅ `RUNTIME_PROVIDER=stub` is default
- Real OpenCode server: ✅ NOT started, NOT run
- All tests via mocked/fake HTTP/SSE: ✅
- No write/edit/bash/git/deploy/migrate/env/secrets: ✅
