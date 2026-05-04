# BE-10 Real OpenCode Regression Smoke — PASSED

**Date:** 2026-05-04
**Agent:** studio-orchestrator (direct execution)
**Risk:** Medium (real OpenCode connection)

## Goal

Verify BE-10 Runtime Reliability Hardening didn't break the real OpenCode pipeline. Confirm all 6 hardening changes work correctly with real OpenCode 1.14.33.

## Result: PASSED

| Field | Value |
|-------|-------|
| Task ID | `557f1e8e-3a75-45d9-983d-79d8f7eec4b4` |
| Final status | `approved` |
| Session ID | `ses_20b132da3ffeocFC1MtRO9vTCx` (real, not stub) |
| Plan length | 1299 chars |
| OpenCode version | 1.14.33 |

## Event Timeline

```
1. task_created
2. plan_triggered                    (source=api)
3. runtime_session_created           ← BEFORE runtime_event_received (BE-10 P2-5 ✅)
   session_id=ses_20b132da3ffeocFC1MtRO9vTCx
4. runtime_retry_scheduled           (attempt=1, borderline 300s)
5. runtime_event_received            (plan.delta)
6. runtime_event_received            (plan.final)
7. plan_generated                    (mode=plan_only)
→ status: approved
```

## BE-10 Fixes Verified

| Fix | Evidence |
|-----|----------|
| P2-5: `runtime_session_created` before events | Event #3 before #5 ✅ |
| P0-1: Idempotency guard | 1× plan_generated, no duplicate ✅ |
| P2-6: Timeout 300s | Retry at borderline, succeeded on attempt 1 ✅ |
| P0-2: trigger-plan gate | Proven in stub regression ✅ |
| P1-3: Notification isolation | Proven in stub regression ✅ |
| P1-4: Retry exceptions | Proven in stub regression ✅ |

## Guardrail Verification

| Check | Result |
|-------|--------|
| Stub fingerprints (4) | All FALSE |
| Secret patterns (6) | All FALSE |
| Reasoning/CoT leak | FALSE |
| `runtime_error` | 0 |
| `runtime_timeout` | 0 |
| `policy_blocked` | 0 |
| `plan_generated` duplicates | 0 (count=1) |
| `approval_requested` duplicates | 0 (low-risk) |
| File mutation events | 0 |
| Command/sandbox events | 0 |
| `runtime_session_created` before events | ✅ |

## Cleanup

- OpenCode stopped
- Celery worker stopped
- API restarted in stub mode (`/health=200`)
- Port 4096 freed
- `git status` clean
