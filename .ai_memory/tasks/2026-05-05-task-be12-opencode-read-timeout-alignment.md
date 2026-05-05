# BE-12: OpenCode Read-Timeout Alignment — DONE

**Date:** 2026-05-05
**Agent:** backend-architect
**Risk:** low
**Scope:** local only; no deploy/migrations/secrets/OpenCode.

## Motivation

Real-world OpenCode 1.14.33 model inference can take 80–170s — well within `RUNTIME_SESSION_TIMEOUT_SECONDS=300` client-side safety net, but beyond the httpx `read_timeout=300` on the transport layer. The OpenCode SDK itself sets `req.timeout=false` (unbounded read) for `POST /session/{id}/message`. AMC's `RealOpenCodeHttpTransport.send_message()` needed the same unbounded read timeout to prevent `httpx.ReadTimeout → OpenCodeTimeoutError("Message request timed out")` before the session/idle timeout logic in `OpenCodeHttpPlanClient` can take over.

## Root Cause

`send_message()` used `_build_client()` which applied `httpx.Timeout(read=300)` — same as the session timeout. Model responses exceeding 300s on the wire would hit `httpx.ReadTimeout`. The SDK avoids this with `req.timeout=false`.

## Changes

### 1. `transport.py` — `send_message()` now creates local `httpx.AsyncClient` with `read=None`

```python
async def send_message(self, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"/session/{session_id}/message"
    timeout_no_read = httpx.Timeout(
        connect=self._connect_timeout,  # 10s — bounded
        read=None,                       # unbounded — SDK-aligned
        write=self._write_timeout,       # 10s — bounded
        pool=self._connect_timeout,     # 10s — bounded
    )
    try:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=timeout_no_read) as client:
            resp = await client.post(url, json=payload)
            ...
    except httpx.ReadTimeout as exc:  # defensive: still maps if somehow raised
        raise OpenCodeTimeoutError(...)
```

Key invariants preserved:
- **`create_session()` unchanged** — still uses `_build_client()` with bounded `read_timeout=300`
- **`_build_client()` unchanged** — local override only in `send_message()`
- **`_build_timeout()` unchanged** — bounded for all other callers
- **Error mapping preserved** — `httpx.ConnectError`, `httpx.HTTPStatusError`, `httpx.ReadTimeout` all still mapped
- **Safety net preserved** — `OpenCodeHttpPlanClient._session_timeout` and `_idle_timeout` remain the authoritative timeout layer

### 2. `test_opencode_transport.py` — updated tests + 5 new BE-12 tests

Updated 6 existing send_message tests to use `@patch("httpx.AsyncClient")` instead of mocking `_build_client` (since `send_message()` no longer calls it).

Added 5 BE-12 tests:
1. `test_be12_send_message_uses_read_none_timeout` — verifies `httpx.AsyncClient` is called with `timeout.read=None`
2. `test_be12_send_message_uses_correct_endpoint` — verifies `POST /session/{id}/message`, no `/prompt`
3. `test_be12_send_message_base_url_preserved` — verifies correct `base_url` passed
4. `test_be12_create_session_still_uses_bounded_read_timeout` — `_read_timeout` still bounded
5. `test_be12_build_client_not_affected` — `_build_timeout()` still bounded

## Verification

| Check | Result |
|-------|--------|
| `python -m compileall app` | PASSED |
| `ruff check app` | No issues |
| `pytest tests/test_opencode_transport.py -v` | **16/16 PASSED** |
| `pytest tests -v` (full suite) | **251/252 PASSED** (1 pre-existing data-collision flake) |
| Real OpenCode server started? | NO |
| `.env`/secrets changed? | NO |
| Deploy/migrations run? | NO |

## Guardrails Confirmed

- Default provider = `stub` (unchanged)
- `RUNTIME_ALLOW_REAL_OPENCODE_HTTP = False` (unchanged)
- `_build_client()` bounded — only `send_message()` unbounded
- Client-side session/idle timeout in `OpenCodeHttpPlanClient` unchanged
- Max plan size, redaction, path confinement, policy_blocked — all unchanged
- `create_session` → `POST /session` (bounded) — unchanged
- `send_message` → `POST /session/{id}/message` (correct endpoint) — unchanged

## Changed Files

1. `apps/api/app/integrations/opencode/transport.py` — `send_message()` refactored
2. `apps/api/tests/test_opencode_transport.py` — 6 tests updated, 5 new BE-12 tests
3. `PROJECT_MEMORY.md` — memory updated
4. `.ai_memory/current_state.md` — state updated
5. `.ai_memory/tasks/2026-05-05-task-be12-opencode-read-timeout-alignment.md` — this file
