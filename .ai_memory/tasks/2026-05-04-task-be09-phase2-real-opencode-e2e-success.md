# BE-09 Phase 2: Real OpenCode E2E — SUCCESS

**Date:** 2026-05-04
**Agent:** studio-orchestrator (coordinated: devops-automator, backend-architect, security-engineer)
**Risk:** Medium (real OpenCode connection, Celery worker)

## Goal

Execute full BE-09 E2E pipeline with real OpenCode 1.14.33:
Worker → API → RealOpenCodeHttpTransport → OpenCode → plan_generated → approved.

## Result: SUCCESS

| Field | Value |
|-------|-------|
| Task ID | `ddc0d397-17a3-4511-ae9a-39a571d57abb` |
| Final status | `approved` |
| Session ID | `ses_20b75bd21ffekkZ4XA2rr4a5Sc` (real, not stub) |
| Plan length | 866 chars |
| Elapsed | ~70s |
| Worker timeout | `API_TIMEOUT_SECONDS = 300` |
| OpenCode version | 1.14.33 |
| Transport | `RealOpenCodeHttpTransport` |

## Event Timeline

```
task_created
  → plan_triggered
  → runtime_retry_scheduled (attempt=1, same session)
  → runtime_event_received (plan.delta)
  → runtime_event_received (plan.final)
  → runtime_session_created
  → plan_generated
```

## Guardrail Verification

| Check | Result |
|-------|--------|
| Stub fingerprints (4) | All FALSE |
| Reasoning/CoT leak (2) | All FALSE |
| Secret patterns (6) | All FALSE |
| File mutation events | None |
| Command/sandbox events | None |
| `runtime_error` | Absent |
| `policy_blocked` | Absent |
| Approval bypass | Not attempted |
| Status `approved` for `risk=low` | Correct |

## Finding: Retry Before Success

`runtime_retry_scheduled` (attempt=1) on same session `ses_20b75bd21ffe...` — timing borderline at 180s session timeout. Retry completed successfully; plan generated on second attempt.

**Severity:** Low (non-blocking). Retry is working correctly. Consider increasing `RUNTIME_SESSION_TIMEOUT_SECONDS` from 180 → 240-300s for stability in BE-10 hardening.

## Where BE-09 Phase 1 Fix Was Critical

Worker `API_TIMEOUT_SECONDS=300` (was 30) — without this fix, worker would have timed out at 30s before plan generation completed at ~70s. The fix directly enabled this E2E success.

## Cleanup

- OpenCode stopped
- Celery worker stopped
- API restarted in `stub` mode
- Port 4096 freed
- `git status` clean

## Security Review

**Verdict: PASSED** (security-engineer, 10/10 checks)

## Follow-up Tasks

- **BE-10:** Increase `RUNTIME_SESSION_TIMEOUT_SECONDS` from 180 → 240-300s for retry-free stability
- **BE-10:** Consider narrowing `autoretry_for` to exclude permanent HTTP errors (404/422)
- **BE-10:** Add idempotency lock on `enqueue_agent_plan`
