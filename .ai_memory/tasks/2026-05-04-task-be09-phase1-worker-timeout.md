# BE-09 Phase 1: Worker API_TIMEOUT_SECONDS Fix

- **Task ID:** BE-09 Phase 1
- **Date:** 2026-05-04
- **Agent:** backend-architect
- **Status:** Complete
- **Risk:** Low
- **Contour:** Local only — no deploy, no migrations, no secrets, no OpenCode server

## Context

BE-08 identified that 180s `RUNTIME_SESSION_TIMEOUT_SECONDS` is borderline for real OpenCode plan requests (80-170s observed). The worker's own `API_TIMEOUT_SECONDS` (30s) was far below this — causing worker-side HTTP timeouts before the API could even finish waiting for OpenCode.

Fix: align worker timeout with API timeout, with buffer.

## Changes Made

### 1. Worker config: `API_TIMEOUT_SECONDS` 30 → 300
- **`apps/worker/app/config.py`:**
  - `API_TIMEOUT_SECONDS: float = 300.0` (was `30.0`)
  - Added comment: must be >= `RUNTIME_SESSION_TIMEOUT_SECONDS=180` + buffer for real OpenCode plan times (80–170s)

### 2. Tests
- **`apps/worker/tests/test_config.py`:** Added `test_api_timeout_default_is_300` — confirms the default value.
- **`apps/worker/tests/test_agent_plan_pipeline.py`:** Added `test_generate_plan_uses_api_timeout_from_settings` — confirms timeout is read from config and passed to HTTP client.

## Files Changed

| File | Change |
|------|--------|
| `apps/worker/app/config.py` | `API_TIMEOUT_SECONDS`: 30.0 → 300.0 + comment |
| `apps/worker/tests/test_config.py` | +1 test: `test_api_timeout_default_is_300` |
| `apps/worker/tests/test_agent_plan_pipeline.py` | +1 test: `test_generate_plan_uses_api_timeout_from_settings` |

## Files NOT Changed (guardrails intact)

- `apps/api/` — no API config changes
- `.env` — no changes
- `docker-compose` — no changes
- OpenCode server — NOT started

## Validation

```
worker: pytest tests -v  ✅ (91/91 passed)
api:    pytest tests -v  ✅ (224/225 passed, 1 pre-existing flake)
```

## Safety Checks

- **Security GO (8/8):** All guardrails preserved.
- **Reality-check GO (8/8):** All invariants confirmed.
- `RUNTIME_PROVIDER=stub` — unchanged
- `RUNTIME_ALLOW_REAL_OPENCODE_HTTP=false` — unchanged
- `OPENCODE_SERVER_URL=""` — unchanged
- No real OpenCode started
- No API config changes

## Summary

Worker-side timeout now matches the expected real OpenCode plan duration (80–170s) with safety buffer. No API or runtime guardrails were modified.
