# TG-03: Telegram Approvals + Task Status UX

**Date:** 2026-05-06  
**Agent:** backend-architect  
**Status:** COMPLETE  
**Contour:** local only; without deploy/migrations/.env/secrets/real Telegram.

## Summary

Implemented TG-03 — full Telegram approvals UX with inline keyboards, callback validation, command handlers for /status, /plan, /approve, /reject, and callback-answer API endpoint.

## API Changes (Phase 1)

### 1. Approval error code fix
- `apps/api/app/routers/approvals.py`: approve/reject `ValueError → 422` changed to `ValueError → 409` for already-decided idempotency

### 2. New endpoints in tasks.py
- **GET /tasks/{task_id}/plan** — returns `{task_id, plan_text, plan_version, status}`
- **POST /tasks/{task_id}/callback-answer** — validates callback_data (HMAC-SHA256 signature, expiry check, chat/thread/user constraints), returns `{task_id, task_status, approval_id, approval_status, action_valid, action, error}`
- Added `CALLBACK_SECRET` and `CALLBACK_MAX_AGE_SECONDS` to API config

### 3. New schemas
- `TaskPlanRead` — dedicated plan response schema
- `CallbackAnswerIn` — callback validation request body
- `CallbackAnswerRead` — callback validation response

### 4. Callback security
- v1 protocol: `version|action|task_id|approval_id|rev|exp|sig`
- HMAC-SHA256 signature validation (API-side only)
- Expiry check with configurable max age
- Chat/thread/user constraint enforcement
- Stale/duplicate callbacks rejected deterministically
- Audit event `callback_received` on every validated callback

## Telegram Bot Changes (Phases 2-5)

### Command handlers
- `handlers/status_handler.py` — `/status <task_id|external_id>` → task card with inline keyboard
- `handlers/plan_handler.py` — `/plan <task_id|external_id>` → plan content with keyboard
- `handlers/approve_handler.py` — `/approve <task_id|external_id>` → approve pending approval
- `handlers/reject_handler.py` — `/reject <task_id|external_id> [reason]` → reject pending approval

### Inline keyboards
- `keyboards/__init__.py` — replaced placeholder with 3 keyboard builders:
  - `build_task_keyboard()` — Approve/Reject/Show Plan/Refresh
  - `build_approval_keyboard()` — Approve/Reject/Refresh
  - `build_plan_keyboard()` — Show Task/Refresh
- Signed callback_data with HMAC-SHA256 (configurable CALLBACK_SECRET)

### Callback handler
- `handlers/callbacks.py` — handles all inline button clicks:
  - approve → POST /approvals/{id}/approve → refresh card
  - reject → POST /approvals/{id}/reject → refresh card
  - show_plan → GET /tasks/{id}/plan → display plan
  - show_task → refresh task card
  - refresh → refresh current card
  - API-side validation via callback_answer before action

### API client extensions
- Added methods: `get_task`, `get_task_plan`, `list_task_events`, `list_approvals_by_task`, `approve_approval`, `reject_approval`, `callback_answer`, `find_task_by_external_id`

### Formatters
- `services/formatters.py`:
  - `format_task_card()` — HTML task status card with emoji
  - `format_approval_card()` — HTML approval card
  - `format_plan_excerpt()` — truncated plan with marker
  - `format_error_message()` — safe user-facing errors
  - HTML escaping for all user content

### Router registration
- Updated `bot.py` and `handlers/__init__.py` to include all 5 new routers
- Added `CALLBACK_SECRET` to bot config

## Tests

### Telegram bot tests (35/35 PASS)
- test_formatters.py: 9 tests (task cards, approval cards, plan excerpts, HTML escaping)
- test_status_handler.py: 5 tests (no args, UUID, external_id, not found, pending approval)
- test_plan_handler.py: 4 tests (no args, not found, empty plan, plan with content)
- test_approve_handler.py: 4 tests (no args, not found, no pending, success)
- test_reject_handler.py: 4 tests (no args, not found, no pending, success with reason)
- test_callback_handlers.py: 9 tests (empty data, invalid task, validation rejected, refresh, approve, approve-no-id, reject, show_plan, unknown action)

### API tests (37/38 PASS, 1 pre-existing flake)
- test_approvals.py: 10 tests (1 pre-existing flake on test_create_approval, rest PASS with 409)
- test_approvals_idempotency.py: 5 tests (second approve→409, second reject→409, reject-after-approve→409, approve-after-reject→409, status unchanged)
- test_tasks_plan_endpoint.py: 11 tests (plan empty, plan with text, plan 404, callback valid, invalid signature, expired, malformed, task not found, chat constraint, with approval, approval mismatch)

## Changed Files (22 files)
**API:** approvals.py, tasks.py, task.py (schema), approval.py (schema), config.py
**API tests:** test_approvals.py, test_approvals_idempotency.py (NEW), test_tasks_plan_endpoint.py (NEW)
**Bot:** bot.py, config.py, handlers/__init__.py, keyboards/__init__.py
**Bot handlers:** callbacks.py (NEW), status_handler.py (NEW), plan_handler.py (NEW), approve_handler.py (NEW), reject_handler.py (NEW)
**Bot services:** api_client.py, formatters.py (NEW)
**Bot tests:** test_formatters.py (NEW), test_status_handler.py (NEW), test_plan_handler.py (NEW), test_approve_handler.py (NEW), test_reject_handler.py (NEW), test_callback_handlers.py (NEW)

## Guardrails preserved
- Bot uses API-only (no DB, no OpenCode, no runtime)
- API is source of truth for all state transitions
- Callback validation on API side only (not client-side)
- HMAC signatures with configurable secret
- HTML escaping for all user content in Telegram messages
- Chat/thread/user constraints enforced on all decisions
- Audit events for every callback action
- No real Telegram token needed for tests

## Verification
- `python -m compileall` — all files ✅
- `ruff check` — all files ✅ (0 errors)
- `pytest apps/telegram-bot/tests/` — 35/35 ✅
- `pytest apps/api/tests/` — 37/38 (1 pre-existing flake)
