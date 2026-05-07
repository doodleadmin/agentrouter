# Task: SEC-02 Phase 2 — Security Audit DB Model, Migration, and Service

**Date:** 2026-05-08
**Agent:** security-engineer
**Status:** completed
**Risk level:** low (read-only, no deploy/migrations run, no secrets, no live services)

## Goal

Implement the infrastructure for the security audit trail: DB model, Alembic migration, append-only service, and redaction helpers.

## What was done

### New files (4)

1. **`apps/api/app/models/security_audit.py`** — `SecurityAuditEvent` SQLAlchemy model (21 columns)
   - id (UUID PK), event_type, actor_type, actor_id, source, action, decision (allowed/denied/error), audit_code, reason
   - task_id (FK→tasks), approval_id (FK→approvals), project_id (FK→projects), agent_id (FK→agents) — all nullable, SET NULL on delete
   - chat_id, thread_id (BigInteger, nullable) — Telegram context
   - ip_hash (SHA-256), correlation_id (UUID), request_id, metadata (JSONB), error_code
   - created_at (timestamptz) — no updated_at (append-only)

2. **`apps/api/alembic/versions/0002_add_security_audit_events.py`** — Alembic migration (additive only)
   - Revision: `0002_add_security_audit_events`
   - Down revision: `0001_initial_all_tables`
   - Creates `security_audit_events` table with 5 indexes, 4 FK constraints (all SET NULL on delete)
   - Downgrade: drops indexes then table
   - No changes to existing tables/data

3. **`apps/api/app/services/audit_service.py`** — `SecurityAuditService` (append-only)
   - `record(event)` — validates + writes, raises on error
   - `record_best_effort(session, event)` — static, non-blocking, returns None on failure
   - `query_by_task(task_id, limit=100)` — events for task
   - `query_by_actor(actor_id, days=30)` — events by actor within time window
   - `query_by_decision(decision, limit=100)` — filter by allowed/denied/error

4. **`apps/api/tests/test_security_audit.py`** — 34 unit tests
   - Model tests (7): field validation, enum constraints, FK default behavior
   - Service tests (14): record, record_best_effort, query methods
   - Redaction helper tests (9): text redaction, metadata sanitization, IP hashing
   - Migration tests (4): table exists, indexes exist, FK constraints, rollback

### Modified files (1)

- **`apps/api/app/models/__init__.py`** — registered `SecurityAuditEvent`

### Redaction helpers

- `redact_text(value)` — strips bot tokens, Bearer tokens, JWTs, API keys, password/secret assignments
- `sanitize_metadata(dict)` — removes raw_callback_data, raw_body, authorization, token, api_key, secret keys
- `hash_ip(ip)` — SHA-256 truncated to 32 hex chars; None-safe

### Validation results

- **API:** 331/331 passed (297 existing + 34 new audit tests)
- **Bot:** 79/79 passed (unchanged)
- **Worker:** 98/98 passed (unchanged)
- **Total:** 508/508
- **Ruff:** clean

### Not done (Phase 3)

- No wiring into approve/reject/permission/callback endpoints
- No Telegram bot changes
- No Worker changes
- Migration NOT run against any real database (only validated via `alembic upgrade head --sql`)

## Changed files

| File | Action |
|------|--------|
| `apps/api/app/models/security_audit.py` | NEW |
| `apps/api/alembic/versions/0002_add_security_audit_events.py` | NEW |
| `apps/api/app/services/audit_service.py` | NEW |
| `apps/api/tests/test_security_audit.py` | NEW |
| `apps/api/app/models/__init__.py` | MODIFIED |

## Result

SEC-02 Phase 2 provides the complete append-only security audit trail infrastructure. The model, migration, and service are ready for Phase 3 wiring into actual endpoint flows (approve/reject, permission checks, callback validation).

## Open questions

- Ready to wire `SecurityAuditService` into approve/reject/permission/callback endpoints (Phase 3)
- Future: Add periodic cleanup/retention policy for old audit events
- Future: Add real embedding model for ip_hash (currently SHA-256)

## Follow-up tasks

- **SEC-02 Phase 3:** Wire audit_service.record() into API endpoint flows (approve, reject, callback-answer, trigger-plan, permission decisions)

## Memory checkpoint

- **Memory updated:** yes
- **Files updated:** PROJECT_MEMORY.md, .ai_memory/current_state.md, .ai_memory/_INDEX.md, .ai_memory/tasks/2026-05-08-task-sec02-phase2-audit-model-service.md
- **Skipped reason:** N/A
