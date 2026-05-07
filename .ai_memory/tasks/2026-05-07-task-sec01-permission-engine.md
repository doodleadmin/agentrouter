# Task Log: SEC-01 Phase 2 — Permission Engine MVP

**Date:** 2026-05-07
**Agent:** security-engineer
**Goal:** Implement centralized Permission Engine with fail-closed design and wire to critical API endpoints.
**Risk level:** low (no .env changes, no live services, no DB changes, no migrations)
**Final status:** COMPLETE

---

## Background

SEC-01 Phase 1 established the security foundation: risk-level rules, agent permission policies, approval flow, and secret redaction. However, enforcement was scattered across routers with ad-hoc checks — there was no centralized permission system.

Phase 2 goal: Create a single `PermissionEngine` that all endpoints can call, with fail-closed behavior (unknown/undefined = denied), and wire it to the 5 most critical endpoints.

---

## Implementation

### Package Created: `apps/api/app/security/`

| File | Purpose |
|------|---------|
| `__init__.py` | Package init, exports `PermissionEngine`, `PermissionAction`, `PermissionDecision`, `PermissionContext` |
| `permissions.py` | Core engine — `PermissionEngine` class, `PermissionAction` enum (14 actions), `PermissionDecision` + `PermissionContext` Pydantic models |
| `context.py` | Helper factories — `context_for_telegram_user`, `context_for_system`, `context_for_callback` |

### Permission Rules Implemented

| Action | Rule | Rationale |
|--------|------|-----------|
| `can_approve` | Admin-gated: `actor_id` must be in `TELEGRAM_ADMIN_USER_IDS`; empty list = fail-closed (deny all) | Only admins can approve tasks |
| `can_reject` | Same as `can_approve` | Only admins can reject tasks |
| `can_trigger_plan` | LOW→`allowed`, MEDIUM→`allowed`+`requires_approval`, HIGH/CRITICAL→`denied`; missing context→`denied` | Risk-based gating; no context = no permission |
| `can_update_status` | SYSTEM→`allowed`, USER→`allowed`+`requires_approval`, others→`denied` | Only trusted actors can mutate task state |
| `can_create_task` | Always `allowed` (stub) | Deferred to Phase 3 |
| `can_execute_runtime` | Always `allowed` (stub) | Deferred to Phase 3 |
| `can_access_project` | Always `allowed` (stub) | Deferred to Phase 3 |
| `can_write_memory` | Always `allowed` (stub) | Deferred to Phase 3 |
| `can_cancel_task` | Always `allowed` (stub) | Deferred to Phase 3 |
| `can_callback_validate` | Always `allowed` (stub) | Deferred to Phase 3 |
| `can_modify_project` | Always `allowed` (stub) | Deferred to Phase 3 |
| `can_modify_agent` | Always `allowed` (stub) | Deferred to Phase 3 |
| Unknown action | Always `denied` | Fail-closed design |

### Endpoints Wired (5)

1. **`POST /approvals/{id}/approve`** — Before approving, calls `engine.check(can_approve, context)`. If denied → 403 Forbidden. Uses `approved_by` query param as actor_id.
2. **`POST /approvals/{id}/reject`** — Same pattern with `rejected_by`.
3. **`POST /tasks/{id}/trigger-plan`** — Calls `engine.check(can_trigger_plan, context)`. Risk level from task. Optional `triggered_by` param.
4. **`POST /tasks/{id}/callback-answer`** — For approve/reject callbacks, checks `telegram_user_id` against admin list.
5. **`PATCH /tasks/{id}/status`** — System actor check for internal status transitions.

### Config Change

`apps/api/app/config.py` — Added `TELEGRAM_ADMIN_USER_IDS: str = ""` (comma-separated). Validated: empty string → empty set (fail-closed).

---

## Files Changed

| # | File | Action | Description |
|---|------|--------|-------------|
| 1 | `apps/api/app/security/__init__.py` | **NEW** | Package init, exports |
| 2 | `apps/api/app/security/permissions.py` | **NEW** | PermissionEngine, PermissionAction enum (14), PermissionDecision, PermissionContext |
| 3 | `apps/api/app/security/context.py` | **NEW** | context_for_telegram_user, context_for_system, context_for_callback |
| 4 | `apps/api/tests/test_security_permissions.py` | **NEW** | 19 unit tests |
| 5 | `apps/api/app/config.py` | Modified | Added TELEGRAM_ADMIN_USER_IDS config |
| 6 | `apps/api/app/routers/approvals.py` | Modified | Wired can_approve/can_reject |
| 7 | `apps/api/app/routers/tasks.py` | Modified | Wired can_trigger_plan, can_update_status, callback approve/reject |
| 8 | `apps/api/app/routers/runtime.py` | Modified | Added TODO comment for future wiring |
| 9 | `apps/api/tests/conftest.py` | Modified | Added `_set_admin_ids` autouse fixture |
| 10 | `apps/api/tests/test_approvals.py` | Modified | Updated + 2 non-admin deny tests |
| 11 | `apps/api/tests/test_approvals_idempotency.py` | Modified | Updated for new behavior |
| 12 | `apps/api/tests/test_tasks_plan_endpoint.py` | Modified | Updated callback test |

**Total:** 12 files (4 new, 8 modified)

---

## Validation Results

| Suite | Before | After | Delta |
|-------|--------|-------|-------|
| API pytest | 275 | 297 | +22 (19 unit + 3 integration) |
| Telegram-bot pytest | 79 | 79 | 0 (unchanged) |
| Worker pytest | 98 | 98 | 0 (unchanged) |
| Ruff | clean | clean | — |
| compileall | clean | clean | — |

---

## Known Limitations (Phase 3 Deferrals)

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| Agent permissions JSONB not read by code | Agent-specific permissions in DB are decorative | No agent can bypass engine rules |
| Runtime/memory/project access stubs | No restriction on runtime execution, memory access, project access | Medium-term — wire when sandbox/prod is stable |
| `can_update_status` USER flag not enforced at endpoint | USER actor can still call PATCH /status without approval | Low priority — current callers are SYSTEM |
| No DB schema changes | Permission rules are code-only, not configurable at runtime | Acceptable for MVP |
| No migrations | — | Not needed |

---

## Security Confirmation

- ✅ No secrets exposed
- ✅ No .env changes
- ✅ No live Telegram/OpenCode/Deploy
- ✅ Compact callback protocol preserved
- ✅ Admin gate fail-closed preserved
- ✅ Unknown actions always denied

---

## Next Steps (SEC-01 Phase 3)

1. Wire runtime/memory/project access permissions (replace stubs)
2. Read agent permissions JSONB from DB
3. Enforce `can_update_status` USER flag at endpoint level
4. Add DB schema for permission rules (if needed)
5. Add permission audit events

---

## Memory Checkpoint

- **Memory updated:** yes
- **Files updated:** `PROJECT_MEMORY.md`, `.ai_memory/current_state.md`, `.ai_memory/_INDEX.md`, `.ai_memory/tasks/2026-05-07-task-sec01-permission-engine.md`
- **Commit hash:** pending
