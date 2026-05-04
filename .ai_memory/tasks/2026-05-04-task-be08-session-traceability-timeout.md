# BE-08: OpenCode Session Traceability + Timeout Tuning

- **Task ID:** BE-08
- **Date:** 2026-05-04
- **Agent:** backend-architect
- **Status:** Complete
- **Risk:** Low
- **Contour:** Local only — no deploy, no migrations, no secrets, no OpenCode server

## Context

BE-08 inspection confirmed: OpenCode 1.14.33 auto-detects workspace from CWD and IGNORES `directory/cwd/path/workspace/mode/model` fields in `POST /session`. Only `title` field is accepted and stored.

BE-07+ smoke showed timeout after 60s — parts-based message payload was accepted (no 400), but OpenCode didn't respond in time.

## Changes Made

### 1. Session payload — `title` field only
- **`apps/api/app/integrations/opencode/schemas.py`:** Added `OpenCodeSessionCreateRequest(title: Optional[str])` schema and `task_title: str = ""` field to `RuntimePlanContext`.
- **`apps/api/app/integrations/opencode/client.py`:** `generate_plan()` now sends `{"title": context.task_title or "Plan task"}` for `POST /session`. Removed ignored fields: mode, correlation_id, idempotency_key, input.
- **`apps/api/app/services/runtime_service.py`:** Passes `task_title=task.title` when building context.

### 2. Timeout increase: 60s → 180s
- **`apps/api/app/config.py`:** `RUNTIME_SESSION_TIMEOUT_SECONDS` changed from 60 to 180.

### 3. Tests
- **`apps/api/tests/test_opencode_transport.py`:** Added 2 tests: payload includes `title`, payload excludes forbidden fields (directory/cwd/path/workspace/mode/model/capabilities/restrictions/projectID/agent).
- **`apps/api/tests/test_runtime_be04.py`:** Added 4 tests: timeout config default = 180, timeout maps to runtime_error/task_failed, default provider still stub, real OpenCode not started.

### 4. Docs
- **`docs/smoke-test-opencode.md`:** Updated session contract (title-only payload, timeout 180s), preflight probe uses `{"title": "Smoke test probe"}`.

### 5. Memory
- Updated: PROJECT_MEMORY.md, .ai_memory/current_state.md, .ai_memory/_INDEX.md

## Files Changed

| File | Change |
|------|--------|
| `apps/api/app/config.py` | `RUNTIME_SESSION_TIMEOUT_SECONDS`: 60 → 180 |
| `apps/api/app/integrations/opencode/schemas.py` | Added `OpenCodeSessionCreateRequest`, `task_title` to `RuntimePlanContext` |
| `apps/api/app/integrations/opencode/client.py` | Session payload → title-only |
| `apps/api/app/services/runtime_service.py` | Pass `task_title=task.title` |
| `apps/api/tests/test_opencode_transport.py` | +2 BE-08 payload shape tests |
| `apps/api/tests/test_runtime_be04.py` | +4 BE-08 guard tests |
| `docs/smoke-test-opencode.md` | Updated session contract + timeout |
| `PROJECT_MEMORY.md` | Added BE-08 entry |
| `.ai_memory/current_state.md` | Added BE-08 status |
| `.ai_memory/_INDEX.md` | Task log count 39→40, added BE-08 entry |
| `.ai_memory/tasks/2026-05-04-task-be08-session-traceability-timeout.md` | This file |

## POST /session Payload Shape (new)

```json
{"title": "Plan endpoint task"}
```

## Not Included (confirmed ignored by OpenCode 1.14.33)

- directory, cwd, path, workspace
- mode, model
- capabilities, restrictions, projectID, agent

## Timeout Config

| Setting | Before | After |
|---------|--------|-------|
| `RUNTIME_SESSION_TIMEOUT_SECONDS` | 60 | **180** |
| `RUNTIME_IDLE_TIMEOUT_SECONDS` | 20 | 20 (unchanged) |

## Validation

```
python -m compileall app  ✅
ruff check app            ✅
pytest tests -v           ✅ (224/225 passed; 1 pre-existing data collision)
```

## Guardrails Confirmed

- [x] Default provider = stub
- [x] Fail-closed on unknown provider
- [x] Path confinement preserved
- [x] Redaction preserved
- [x] max_plan_size enforced
- [x] plan-only policy enforced
- [x] No silent fallback
- [x] Real OpenCode server NOT started
- [x] No directory/cwd/path/workspace/mode/model in session payload
- [x] No .env/secrets/migrations/deploy
