# Task: BE-08 Real OpenCode Smoke — SUCCESS

**Date:** 2026-05-04
**Agent:** backend-architect (execution), studio-orchestrator (memory recording)
**Status:** ✅ PASSED (security review complete, GO)

## Summary

First successful end-to-end `plan_generated` from **real OpenCode 1.14.33** (not stub, not fake). The smoke test proved the full guardrail chain works correctly with a live OpenCode server.

## Smoke execution data

| Field | Value |
|-------|-------|
| task_id | `46482979-bd51-4b28-b4d3-d5230ae2117f` |
| final status | `approved` |
| session_id | `ses_20bbf3443ffe9jGPUiUrGNkS7G` |
| OpenCode version | 1.14.33 |
| plan_text length | 875 chars |
| plan excerpt | Real analysis covering healthcheck endpoint, tests, Docker HEALTHCHECK, probes |
| stub fingerprints | ABSENT |
| reasoning leak | ABSENT |
| file/command/sandbox events | ABSENT |
| policy_blocked | ABSENT |
| runtime_error | ABSENT |

## Event timeline

1. `task_created`
2. `runtime_retry_scheduled` — first attempt timed out at ~180s, second succeeded
3. `runtime_event_received` ×2
4. `runtime_session_created`
5. `plan_generated`
6. status → `approved`

## Architecture insights

- Event ordering (`retry_scheduled` BEFORE `session_created`) is architecturally correct: client emits retry during `generate_plan()`, service emits `session_created` after successful plan completion.
- The retry was triggered in the client (timeout occurred before session was fully confirmed), then the second attempt successfully completed the session and generated the plan.

## Prerequisites that made this possible

1. **BE-07+** — native contract alignment (OpenCode 1.14.33 `parts`-based message format)
2. **BE-08** — session traceability (`title` field in `POST /session` payload)
3. **BE-08** — timeout increase (60→180s, which turned out borderline — see finding below)
4. **DEV-DB-01** — async Alembic migration fix (enabled clean DB state for testing)

## Finding (medium, non-blocking)

`runtime_retry_scheduled` was triggered before successful `plan_generated`. This indicates the 180s timeout is borderline. **Recommendation:** consider increasing `RUNTIME_SESSION_TIMEOUT_SECONDS` from 180 to 300 in a follow-up hardening task.

## Cleanup

- OpenCode stopped
- API returned to stub mode
- git status clean
- no .env / code / persistent env changes

## Safety verification

- ✅ No file mutation
- ✅ No command execution
- ✅ No sandbox events
- ✅ No secret leakage
- ✅ localhost-only (127.0.0.1:4096 and 127.0.0.1:8000)
- ✅ No stub fingerprints in plan_text (real analysis content)

## Key takeaway

The AMC → OpenCode integration pipeline is now **proven end-to-end**:

```
Task creation → Trigger plan → Celery agent_plan → RuntimeService → 
OpenCodeHttpClient → RealOpenCodeHttpTransport → OpenCode 1.14.33 →
plan.final → plan_generated event → task.status=approved
```

All guardrails (fail-closed, path confinement, redaction, max_plan_size, plan-only) were exercised and held.

## Follow-up recommended

- Increase `RUNTIME_SESSION_TIMEOUT_SECONDS` from 180 → 300s to eliminate borderline retry
- Consider adding `runtime_session_timeout` metric for observability
