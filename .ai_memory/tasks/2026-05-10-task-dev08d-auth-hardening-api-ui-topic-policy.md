# DEV-08D: Mini App Auth Hardening + API-backed UI Flow + Topic Role Policy

**Date:** 2026-05-10
**Status:** completed
**Agents:** studio-orchestrator
**Risk:** low (local code only)

## Summary

Hardened Telegram Mini App auth, added API-backed frontend flows with proper state management, and formalized topic role policy validation.

## Changes

### 1. Auth Hardening (Backend)
- **File:** `apps/api/app/services/telegram_webapp_auth.py`
  - Added `auth_date` freshness check: rejects initData older than 300s (configurable `max_age_seconds`)
  - Added future `auth_date` rejection
  - Added `_derive_session_token()` — deterministic SHA256 token from verified hash + bot token
  - Response now includes `session_token` field for replay-protection foundation
  - `_now` parameter for deterministic testing

### 2. Auth Schema Update
- **File:** `apps/api/app/schemas/telegram_webapp.py`
  - `TelegramWebAppAuthResponse` now includes `session_token: str`

### 3. Topic Role Policy (Backend)
- **File:** `apps/api/app/services/telegram_topic_policy.py` (NEW)
  - `VALID_TOPIC_KINDS` frozenset: `general | agent | approvals | system_logs | task`
  - `validate_topic_policy()` enforces:
    - `agent` kind requires `agent_id`
    - `task` kind requires `project_id`
    - Invalid kind returns violation (short-circuits)
  - `TopicPolicyViolation` frozen dataclass for structured error reporting

### 4. Auth Tests (expanded from 3 → 12)
- **File:** `apps/api/tests/test_telegram_webapp_auth.py`
  - 12 tests covering: valid auth, invalid signature, missing initData, stale initData, future auth_date, tampered payload, missing hash, missing user, malformed JSON, no bot token, boundary freshness, deterministic session token

### 5. Topic Policy Tests (NEW, 14 tests)
- **File:** `apps/api/tests/test_telegram_topic_policy.py` (NEW)
  - 14 tests covering: all valid kinds, agent-kind-without-agent_id violation, task-kind-without-project_id violation, invalid kind, short-circuit behavior, both-bindings pass, frozen dataclass

### 6. Topic Schema Tests (expanded from 5 → 8)
- **File:** `apps/api/tests/test_telegram_topics.py`
  - Added: task_kind_with_project_id, approvals_kind, system_logs_kind, update_kind

### 7. Frontend — Types (rewritten)
- **File:** `apps/web/src/types.ts`
  - Full alignment with backend schemas: `Agent`, `TaskItem`, `ApprovalItem`, `EventItem`, `SystemStatus`
  - Derived UI types: `AgentSummary`, `TaskSummary`, `SystemStatusSummary`
  - `ApiState<T>` discriminated union for loading/error/empty/success

### 8. Frontend — API Client (rewritten)
- **File:** `apps/web/src/api/client.ts`
  - Session token management (get/set)
  - `apiFetch()` with auth header injection
  - Transformers: `agentToSummary()`, `taskToSummary()`, `statusToSummary()`
  - Real endpoint paths: `/agents`, `/tasks`, `/approvals`, `/events`, `/health`
  - `useApi<T>()` hook with loading/error/empty/success states + `refetch()`

### 9. Frontend — Mock Data (updated)
- **File:** `apps/web/src/api/mockData.ts`
  - Updated shapes to match new types (AgentSummary, TaskSummary, EventItem, SystemStatus)

### 10. Frontend — Pages (all updated with loading/error/empty states)
- `apps/web/src/pages/HomePage.tsx` — uses `useApi` for status/agents/activity
- `apps/web/src/pages/AgentsPage.tsx` — loading → empty → list → error
- `apps/web/src/pages/TasksPage.tsx` — risk + status pills, loading/error/empty
- `apps/web/src/pages/AgentDetailPage.tsx` — loading → error → empty → detail
- `apps/web/src/pages/MorePage.tsx` — shows session token status

### 11. Frontend — Components (updated for new types)
- `StatusCard.tsx` — uses `SystemStatusSummary`
- `AgentCard.tsx` — uses `AgentSummary`, clickable
- `AgentListItem.tsx` — uses `AgentSummary`, clickable
- `AgentDetailCard.tsx` — uses `Agent` (full), shows permissions JSON
- `ActivityItem.tsx` — uses `EventItem`
- `States.tsx` (NEW) — `LoadingState`, `EmptyState`, `ErrorState` reusable components

### 12. Frontend — Styles
- `apps/web/src/styles.css` — added `.spinner` animation and `.retry-btn`

## Test Results

| Suite | Tests | Status |
|-------|-------|--------|
| API — webapp auth | 12 | ✅ PASS |
| API — topic schemas | 8 | ✅ PASS |
| API — topic policy | 14 | ✅ PASS |
| **DEV-08D subtotal** | **34** | **✅ PASS** |
| Telegram bot | 83 | ✅ PASS |
| Worker | 98 | ✅ PASS |
| Frontend build | — | ✅ PASS |

## Risks
- None: local code only, no deploy, no migrations, no secrets

## Contour
- Local code changes only
- No migrations
- No deploy
- No secrets edits
- Production not touched

## Memory checkpoint
- **Memory updated:** yes
- **Files updated:** task log, PROJECT_MEMORY.md, current_state.md, _INDEX.md
