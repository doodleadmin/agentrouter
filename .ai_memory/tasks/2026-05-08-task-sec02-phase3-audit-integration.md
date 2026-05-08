# Task: SEC-02 Phase 3 — Integrate P0 Security Audit Points

**Date:** 2026-05-08
**Agent:** knowledge-steward (memory recording) / security-engineer (implementation)
**Status:** completed
**Risk level:** low (read-only wiring, best-effort audit, no database changes, no deploy)

## Goal

Wire `SecurityAuditService` into the 4 P0 security-sensitive API endpoints: approve, reject, callback-answer, and trigger-plan permission decisions.

## What was done

### Endpoint wiring (4 endpoints)

| Endpoint | Event Type | Decision | When |
|----------|-----------|----------|------|
| `POST /approvals/{id}/approve` | `permission_denied` | denied | Non-admin user → 403 |
| `POST /approvals/{id}/approve` | `approval_decided` | allowed | Admin approves → 200 |
| `POST /approvals/{id}/reject` | `permission_denied` | denied | Non-admin user → 403 |
| `POST /approvals/{id}/reject` | `approval_decided` | allowed | Admin rejects → 200 |
| `POST /tasks/{id}/callback-answer` | `callback_validated` | denied | Expired/tampered/malformed/unknown/mismatch/permission_denied (6 failure types) |
| `POST /tasks/{id}/callback-answer` | `callback_validated` | allowed | Valid approve/reject callback |

### Implementation details

- **`SecurityAuditService.audit_permission_decision()`** — new async static helper that wraps `record_best_effort()` for permission decision events. Accepts session, permission_context, decision, action, and optional task_id_override.
- **`_determine_callback_failure_type()`** — new helper in `tasks.py` router that maps callback validation failures to descriptive audit reasons (expired, tampered, malformed, unknown_action, external_id_mismatch, permission_denied).
- **`_audit_callback_denied()`** — new async helper for callback deny events, using `_determine_callback_failure_type()`.
- **Wired `approve_approval()`** — allowed: `approval_decided` on success; denied: `permission_denied` on PermissionError (non-admin → 403).
- **Wired `reject_approval()`** — same pattern: `approval_decided` on success; `permission_denied` on PermissionError.
- **Wired `callback_answer()`** — valid callback (allowed): `callback_validated` with action details; invalid callback (denied): `callback_validated` with specific failure type in reason.

### Safety properties

- **Best-effort writes:** `record_best_effort()` used everywhere — audit failure logs a warning but never blocks the primary flow (HTTP response).
- **No raw `callback_data` in metadata:** The compact callback data is never written to audit metadata. Only `action` and `task_external_id` (from the signed payload) are stored.
- **Reason redaction:** All reason strings pass through `redact_text()` before storage (tokens, secrets, JWTs, API keys stripped).
- **Task FK safety:** Denied permission audits for approve/reject use `task_id_override=None` (task context not yet validated when permission denied).

### Changed files (4)

| File | Action | Lines |
|------|--------|-------|
| `apps/api/app/services/audit_service.py` | MODIFIED | +57 |
| `apps/api/app/routers/approvals.py` | MODIFIED | +66 |
| `apps/api/app/routers/tasks.py` | MODIFIED | +156 |
| `apps/api/tests/test_security_audit_integration.py` | NEW | 16 tests |

### Validation results

- **API:** 347/347 passed (was 331, +16 integration tests)
- **Bot:** 79/79 passed (unchanged)
- **Worker:** 98/98 passed (unchanged)
- **Total:** 524/524
- **Ruff:** all clean
- **Compileall:** all clean

### Security

- No secrets exposed
- No `.env` changes
- No live Telegram/OpenCode/Deploy
- No DB schema changes or migrations
- Compact callback protocol preserved (no raw callback_data in audit trail)

### Not done (deferred)

- Worker-side audit events (runtime operations, sandbox execution)
- Agent-specific audit views/dashboards
- Periodic audit cleanup/retention policy
- Real-time audit alerting for denied events

## Result

All 4 P0 security-sensitive API endpoints now emit structured audit events for both allowed and denied decisions. The audit trail records who, what, when, and with what outcome — providing the foundation for security monitoring, compliance auditing, and incident investigation.

## Open questions

- Future: Wire audit into worker-side operations (runtime execution, sandbox, Celery task transitions)
- Future: Add audit search/filter API for admin dashboard
- Future: Real-time alerting on denied permission events (e.g., Telegram notification to admins)

## Follow-up tasks

- **SEC-03:** Worker-side audit events (runtime execution, Celery task transitions)
- **MEM-05:** Audit trail viewing in web dashboard

## Memory checkpoint

- **Memory updated:** yes
- **Files updated:** PROJECT_MEMORY.md, .ai_memory/current_state.md, .ai_memory/_INDEX.md, .ai_memory/tasks/2026-05-08-task-sec02-phase3-audit-integration.md
- **Skipped reason:** N/A
