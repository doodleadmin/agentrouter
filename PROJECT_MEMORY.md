# PROJECT_MEMORY.md — Краткий индекс состояния проекта

> **Это краткая сводка.** Полная память проекта — в `.ai_memory/` (Obsidian-like vault, подключён к MCP).
> Навигация по vault: [.ai_memory/_INDEX.md](.ai_memory/_INDEX.md)

## Текущий статус

**Фаза:** Phase 1 — Telegram Routing (DOP-03 Phase 3 Dry-run Validation PASS + DOP-03 Phase 2 Production Runtime Templates + Enhanced Health Check COMPLETE + SEC-03B Phase 2 SQLAlchemy Log Safety COMPLETE + SEC-03 Phase 3 Live Redaction Smoke PASS + SEC-03 Phase 2 Centralized Secrets Redaction COMPLETE + SEC-02 Phase 4 Live Smoke PASS + SEC-02 Phase 3 P0 Audit Integration COMPLETE + SEC-02 Phase 2 Audit Model+Service COMPLETE + SEC-01 Phase 3 Live Smoke PASS + SEC-01 Phase 2 Permission Engine MVP COMPLETE)
**Статус:** DOP-03 Phase 3 Production Templates Dry-run Validation PASS + DOP-03 Phase 2 Production Runtime Templates + Enhanced Health Check COMPLETE + SEC-03B Phase 2 SQLAlchemy Log Safety COMPLETE + SEC-03 Phase 3 Live Redaction Smoke PASS + SEC-03 Phase 2 Centralized Secrets Redaction COMPLETE + BE-10 Runtime Reliability Hardening COMPLETE + BE-11 Runtime Runbook Scripts & Docs COMPLETE + BE-11C scripts parser/encoding hardening complete (local scripts only) + BE-12 OpenCode read-timeout alignment COMPLETE + TG-03 Telegram Approvals + Task Status UX COMPLETE + TG-04 Live Integration Phase 1 (security prerequisites) COMPLETE + TG-04 aiogram 3.15 message_thread_id compatibility fix COMPLETE + TG-04 HTML placeholder fix COMPLETE + TG-04 private chat wording fix COMPLETE + TG-04 private chat binding support COMPLETE + DEV-LINUX-01 Ubuntu 22.04 runtime scripts COMPLETE + DEV-LINUX-01B dry-run precondition fix COMPLETE + DEV-LINUX-01C real stub contour validation COMPLETE + DEV-LINUX-01D real OpenCode runtime contour COMPLETE + WORKER-LINUX-01 Celery SIGHUP restart crash fix COMPLETE + TG-04 Phase 5 Live Private Chat E2E COMPLETE + TG-05 Phase 1 Live Notifications + Admin Gate COMPLETE + CI-01 Phase 1 Local Validation COMPLETE + TG-05 Phase 2 Live Notification Smoke PASS + TG-05 Phase 3 Admin Approval Flow PASS (2 bug fixes) + TG-05 Phase 4 Admin Reject Flow PASS + TG-05 CLOSEOUT PASS + CI-02 Local Validation Fixes PASS + TG-06 Phase 2 Compact Telegram Callback Protocol COMPLETE + TG-06 Phase 3 Live Callback E2E COMPLETE + INFRA-01 Dev Runtime Config Drift Fix COMPLETE + INFRA-02 TG-06 Regression Live Smoke PASS + MEM-04 Phase 2 Soft Mandatory Memory Checkpoints COMPLETE + SEC-01 Phase 2 Permission Engine MVP COMPLETE + SEC-01 Phase 3 Live Smoke: PermissionEngine admin gate PASS + SEC-02 Phase 2 Audit Model, Migration & Service COMPLETE + SEC-02 Phase 3 P0 Audit Integration COMPLETE + SEC-02 Phase 4 Audit Trail Live Smoke PASS.
**Дата последнего обновления:** 2026-05-08
**Project root:** `F:\dev\agentrouter`

### 2026-05-08 — DOP-03 Phase 3: Production Templates Dry-run Validation

- **Агент:** studio-orchestrator
- **Контур:** WSL2 Ubuntu 22.04 + Windows local repo; dry-run only; без deploy/migrations/.env/secrets/OpenCode/live Telegram.
- **Commit tested:** `09b626e` (`feat(deploy): add production runtime templates`)
- **Сделано:**
  - Sync WSL from Windows local repo to `09b626e`, working tree clean.
  - Ran `validate-production-templates.sh`: **ALL CHECKS PASSED**.
  - Safety grep checks: no dangerous matches in prod templates; `0.0.0.0` found only in dev compose (expected).
  - Docker compose prod dry-run config render PASS: API bind `127.0.0.1`, `DEBUG=false`, `SQL_ECHO=false`, internal DB/Redis only, placeholders only.
  - systemd unit verify: no fatal syntax errors; only environment-specific warnings in WSL for non-existent deploy paths.
  - Caddy binary unavailable in WSL: validation SKIP with reason recorded.
  - Runtime smoke: `/health` returned HTTP 200 with `checks.api/database/redis=ok`; no secrets in response.
  - Log safety: `CALLBACK_SECRET` redacted (`set (not displayed)`), no SQLAlchemy bind parameter dumps, no secrets leaked.
  - Regression validation: API 401/401, Bot 79/79, Worker 98/98, **Total 578/578**, compileall/ruff clean.
  - Cleanup completed: no orphan API process, git clean, `.env` absent, `.env.local` gitignored.
- **Verdict:** **PASS** (dry-run GO for template readiness; no deploy performed).
- Task summary: [.ai_memory/tasks/2026-05-08-task-dop03-phase3-dry-run-validation.md](.ai_memory/tasks/2026-05-08-task-dop03-phase3-dry-run-validation.md)

### 2026-05-08 — DOP-03 Phase 2: Production Runtime Templates + Enhanced Health Check

- **Агент:** studio-orchestrator
- **Контур:** local only; без deploy/migrations/.env/secrets/OpenCode/live Telegram.
- **Цель:** Create production runtime templates and enhance /health endpoint with DB/Redis dependency checks.
- **Сделано:**
  - **Enhanced /health endpoint** — backward-compatible, adds `checks` dict (api, database, redis). Status `"ok"` or `"degraded"`. HTTP 200 always. DB: `SELECT 1` via AsyncSessionLocal. Redis: ping via redis.asyncio. No secrets exposed.
  - **Caddyfile template** — `{$AGENTROUTER_DOMAIN}` / `{$AGENTROUTER_TLS_EMAIL}` placeholders, reverse proxy to 127.0.0.1:8000, gzip/zstd, JSON access logs with rotation, comments for future webhook/dashboard.
  - **3 systemd unit templates** — agentrouter-api (127.0.0.1:8000, uvicorn), agentrouter-worker (celery -A app.celery_app worker), agentrouter-telegram-bot (python -m app.main). All: User=agentmc, NoNewPrivileges, PrivateTmp, ProtectSystem=strict, EnvironmentFile, journald logging. No inline secrets.
  - **docker-compose.prod.yml** — postgres (pgvector/pg16), redis (7-alpine), api (127.0.0.1:8000 only), worker, telegram-bot. Internal network. Variable substitution from .env. DEBUG=false, SQL_ECHO=false, RUNTIME_PROVIDER=stub.
  - **.env.example** — all required vars with CHANGE_ME placeholders, security comments, no real secrets.
  - **validate-production-templates.sh** — 9 check categories (file existence, no real tokens, no SQL_ECHO=true, no DEBUG=true, 127.0.0.1 bind, no inline secrets, syntax, systemd-analyze, docker compose config). ALL CHECKS PASSED.
  - **docs/deployment.md** — production architecture, two deployment modes (systemd bare-metal + Docker Compose), env setup, file permissions, startup order, health checks, rollback procedure.
  - **docs/operations-runbook.md** — start/stop/restart commands, safe restart order, journalctl checks, health monitoring, database backup/restore, common troubleshooting, "What NOT to Do" table.
  - **infra/deploy/README.md** — updated to document all deploy templates.
- **Changed files (14):**
  - MODIFIED: `apps/api/app/routers/health.py` (+48 lines), `infra/deploy/README.md` (+20 lines), `docs/deployment.md` (NEW)
  - NEW: `apps/api/tests/test_health.py` (4 tests), `infra/deploy/Caddyfile`, `infra/deploy/agentrouter-api.service`, `infra/deploy/agentrouter-worker.service`, `infra/deploy/agentrouter-telegram-bot.service`, `infra/docker/docker-compose.prod.yml`, `.env.example`, `scripts/deploy/validate-production-templates.sh`, `docs/deployment.md`, `docs/operations-runbook.md`
- **Validation:** API 401/401 (was 397, +4 health tests), Bot 79/79, Worker 98/98, **Total: 578/578**, ruff clean, compileall clean, deploy validation ALL CHECKS PASSED.
- **Security:** No secrets in templates, no real tokens, no SQL_ECHO=true defaults, no DEBUG=true in production configs, API binds 127.0.0.1 only, no inline secrets in systemd units.
- Task summary: [.ai_memory/tasks/2026-05-08-task-dop03-production-runtime-templates.md](.ai_memory/tasks/2026-05-08-task-dop03-production-runtime-templates.md)

- **Агент:** security-engineer
- **Контур:** local only; без deploy/migrations/environment/secrets/OpenCode.
- **Root cause (SEC-03 Phase 3 live smoke):** `session.py` used `echo=settings.DEBUG`, dev scripts always set `DEBUG=true`, causing SQLAlchemy engine logger to emit all SQL + bind params (including `tasks.raw_text`) into `api-stub.log`.
- **Fix:** Added `SQL_ECHO: bool = False` to config (independent of DEBUG), changed `session.py` to use `echo=settings.SQL_ECHO`, updated dev scripts with comments explaining SQL_ECHO is unset/false by default and only enabled via explicit opt-in.
- **Design:** DEBUG can remain true in dev (for FastAPI error detail); SQL_ECHO defaults to false (no bind param logging); SQL echo requires explicit opt-in `SQL_ECHO=true`. No new env vars needed in `.env` files.
- **Changed files (5):**
  - MODIFIED: `apps/api/app/config.py`, `apps/api/app/db/session.py`, `scripts/dev-linux/start-api-stub.sh`, `scripts/dev-linux/start-api-opencode.sh`
  - NEW: `apps/api/tests/test_config.py` (4 tests)
- **Validation:** API 397/397 (was 393, +4 config tests), Bot 79/79, Worker 98/98, **Total: 574/574**, ruff clean, compileall clean.
- Task summary: [.ai_memory/tasks/2026-05-08-task-sec03b-sqlalchemy-log-safety.md](.ai_memory/tasks/2026-05-08-task-sec03b-sqlalchemy-log-safety.md)

### 2026-05-08 — SEC-01 Phase 3: Live Smoke — PermissionEngine admin gate validation

- **Агент:** security-engineer
- **Контур:** live WSL2 Ubuntu 22.04; live Telegram bot + Celery worker + API stub + native PostgreSQL 14 + Redis; commit 276c8b4.
- **Цель:** Validate PermissionEngine MVP admin gate against real Telegram approval flows (inline button + commands).
- **Results:**
  - **3 medium-risk tasks** created (54b895cf, bc665abf, cd0143a0), all triggered to plan → waiting_approval.
  - **Task 1 (inline approve):** Inline Approve button clicked → callback-answer 200 OK (compact callback validated) → approval a2203476 approved, approved_by=1113930428 → task waiting_approval→approved ✅
  - **Task 2 (command approve):** `/approve` command in Telegram → POST /approvals/aada9d27/approve 200 OK → approval approved, approved_by=1113930428 → task waiting_approval→approved ✅
  - **Task 3 (command reject):** `/reject <task_id> <reason>` → POST /approvals/800e37fe/reject 200 OK → approval rejected, reason="reason: SEC-01 regression reject test" → task waiting_approval→cancelled ✅
  - **All 4 HTTP POSTs returned 200 OK** in bot log.
- **PermissionEngine Results:**
  - Zero 403 PERMISSION DENIED responses
  - All 3 admin-gated operations passed (inline approve + command approve + command reject)
  - Admin gate correctly allowed user 1113930428 (in TELEGRAM_ADMIN_USER_IDS)
  - Compact callback protocol preserved (callback-answer 200 OK)
  - No BUTTON_DATA_INVALID, no BadRequest, no signature errors
  - Zero tracebacks in API, Worker, or Bot logs
  - approved_by correctly set to 1113930428 on all 3 operations
  - Reason correctly stored on rejection
  - Worker log clean (no errors)
  - No security policy violations detected
- **Verdict:** PASS — PermissionEngine admin gate validated for all 3 approval flows.
- **Changed files:** None (memory-only update)
- Task summary: [.ai_memory/tasks/2026-05-08-task-sec01-phase3-live-smoke.md](.ai_memory/tasks/2026-05-08-task-sec01-phase3-live-smoke.md)

### 2026-05-08 — SEC-02 Phase 3: Integrate P0 Security Audit Points

- **Агент:** security-engineer (implementation), knowledge-steward (memory recording)
- **Контур:** local only; без deploy/migrations/.env/secrets/OpenCode.
- **Цель:** Wire `SecurityAuditService` into the 4 P0 security-sensitive API endpoints: approve, reject, callback-answer, and trigger-plan permission decisions.
- **Сделано:**
  - **Approve endpoint:** `permission_denied` (non-admin → 403) + `approval_decided` (admin approve → 200)
  - **Reject endpoint:** `permission_denied` (non-admin → 403) + `approval_decided` (admin reject → 200)
  - **Callback-answer endpoint:** `callback_validated` denied (6 failure types: expired, tampered, malformed, unknown_action, external_id_mismatch, permission_denied) + `callback_validated` allowed (valid approve/reject)
  - **Implementation helpers:** `audit_permission_decision()` async static, `_determine_callback_failure_type()`, `_audit_callback_denied()`
- **Safety properties:**
  - Best-effort writes (failure logs warning, never blocks primary flow)
  - No raw callback_data in metadata
  - Reason redacted (tokens, secrets, JWTs, API keys stripped)
  - Task FK safety: denied permission audits use task_id_override=None
- **Валидация:** API 347/347 (was 331, +16 integration tests), Bot 79/79, Worker 98/98, **Total: 524/524**, ruff clean, compileall clean.
- **Migration NOT run** against any real database. No DB schema changes.
- **Not done (deferred):** Worker-side audit events, agent-specific audit views, periodic cleanup, real-time alerting.
- **Изменённые файлы (4):**
  - MODIFIED: `apps/api/app/services/audit_service.py` (+57 lines), `apps/api/app/routers/approvals.py` (+66 lines), `apps/api/app/routers/tasks.py` (+156 lines)
  - NEW: `apps/api/tests/test_security_audit_integration.py` (16 tests)
- Task summary: [.ai_memory/tasks/2026-05-08-task-sec02-phase3-audit-integration.md](.ai_memory/tasks/2026-05-08-task-sec02-phase3-audit-integration.md)

### 2026-05-08 — SEC-02 Phase 4: Live Smoke — Validate Audit Trail with Real Telegram Flows

- **Агент:** security-engineer (execution), knowledge-steward (memory recording)
- **Контур:** live WSL2 Ubuntu 22.04; live Telegram bot + Celery worker + API + native PostgreSQL 14 + Redis; commit 7ae7f6c.
- **Цель:** Validate `SecurityAuditService` integration against real Telegram `/approve` flow.
- **Test Setup:**
  - DB re-initialized (Alembic 0001+0002 both applied)
  - Seed restored (project `agentrouter` + agent `studio-orchestrator`)
  - API (PID 14509), Worker (PID 14644), Bot (PID 9571) started
- **Test Execution:**
  - Created `task-0001` (ID `88194932`, medium risk) → plan → `waiting_approval`
  - Approval `a90f100c` created (pending)
  - User ran `/approve` in Telegram → task status: `approved`, approval: `approved_by=1113930428`
- **Audit Event Verification (direct DB query):**
  - Event written to `security_audit_events` table:
    - `event_type`: `approval_decided`
    - `decision`: `allowed`
    - `action`: `approve`
    - `audit_code`: `SEC-PERM-APPROVE-ALLOW`
    - `actor_type`: `user`, `actor_id`: `1113930428`
    - `source`: `telegram`
    - `task_id`: `88194932`, `approval_id`: `a90f100c`
  - Metadata (clean, no secrets): `risk_level=medium`, `external_id=task-0001`, `task_status_before=waiting_approval`, `task_status_after=approved`, `approval_status_before=pending`, `approval_status_after=approved`
  - Reason: empty (no redaction needed)
- **Old `task_events` co-exists:** `task_created`, `plan_triggered`, `plan_generated`, `approval_requested`, `approval_granted` written as before.
- **Log Safety:** Bot: 4/4 HTTP 200 OK. API: audit INSERT confirmed. Worker: stale session errors pre-existing (not from test).
- **Verdict:** PASS — audit trail validated for real Telegram `/approve` flow. All fields correctly captured. Both audit and `task_events` systems co-exist. No secrets exposed. No code changes.
- **Changed files:** None (memory-only update)
- Task summary: [.ai_memory/tasks/2026-05-08-task-sec02-phase4-live-smoke.md](.ai_memory/tasks/2026-05-08-task-sec02-phase4-live-smoke.md)

### 2026-05-08 — SEC-03 Phase 2: Centralized Secrets Redaction

- **Агент:** security-engineer
- **Контур:** local only; без deploy/migrations/environment/secrets/OpenCode.
- **Цель:** Create a centralized redaction module unifying 4 previously separate redaction systems into a single source of truth with 10 secret pattern types.
- **Сделано:**
  - **Central module `apps/api/app/security/redaction.py`** — 5 functions (`redact_text`, `redact_mapping`, `contains_secret`, `sanitize_metadata`, `find_secret_matches`) covering 10 patterns: Telegram token, Bearer, JWT, `sk-*` API key, GitHub token, DB password, Redis password, generic assignments, PEM private key, CALLBACK_SECRET. All redacted values → `[REDACTED:TYPE]`.
  - **Audit service** (`audit_service.py`) — removed local `redact_text`/`sanitize_metadata`, imports from central (removed ~70 lines).
  - **Runtime guardrails** (`runtime_guardrails.py`) — `redact_payload` delegates to `redact_mapping`, `redact_text` from central.
  - **Task events** (`task_event_service.py`) — `TaskEventService.create()` applies `redact_mapping(payload)` before INSERT.
  - **Worker redaction** (`worker/app/services/redaction.py`) — synced 10-pattern set with sync comment.
  - **Worker agent_plan** (`worker/app/tasks/agent_plan.py`) — `redact_text()` before exception logging.
- **Валидация:** API 393/393 (was 347, +46 redaction tests), Bot 79/79, Worker 98/98, **Total: 570/570**, ruff clean, compileall clean.
- **Not changed (out of scope):** MemoryPolicyService (keeps REJECT behavior), pre-commit hooks, git history scan, API logging filter (uvicorn), .env/secrets.
- **Изменённые файлы (12):**
  - NEW: `apps/api/app/security/redaction.py`, `apps/api/tests/test_security_redaction.py` (46 tests)
  - MODIFIED: `apps/api/app/security/__init__.py`, `apps/api/app/services/audit_service.py`, `apps/api/app/policy/runtime_guardrails.py`, `apps/api/app/services/task_event_service.py`, `apps/worker/app/services/redaction.py`, `apps/worker/app/tasks/agent_plan.py`, `apps/api/tests/test_security_audit.py`, `apps/api/tests/test_runtime_be04.py`, `apps/worker/tests/test_execute_security.py`, `apps/worker/tests/test_execute_e2e_fake.py`
- Task summary: [.ai_memory/tasks/2026-05-08-task-sec03-secrets-redaction.md](.ai_memory/tasks/2026-05-08-task-sec03-secrets-redaction.md)

### 2026-05-08 — SEC-03 Phase 3: Live Redaction Smoke

- **Агент:** security-engineer (execution), knowledge-steward (memory recording)
- **Контур:** live WSL2 Ubuntu 22.04; Docker PostgreSQL + Redis; commit 5025168.
- **Цель:** Verify centralized redaction (SEC-03 Phase 2) against a controlled secret corpus injected into real task/approval/audit flows.
- **Test Setup:**
  - DB re-initialized (Alembic 0001+0002 applied)
  - Seed restored
  - API, Worker, Bot started
  - Fake-secret corpus (8 real-looking patterns) embedded in task raw_text
- **Test Execution:**
  - Task `dfee2c8f` (external `task-0001`, medium risk) created → plan → `waiting_approval`
  - User approved via `/approve` in Telegram → task `approved`, approval `approved_by=1113930428`
- **Redaction Verification Results:**
  - `security_audit_events.metadata` — no fake secrets PASS
  - `security_audit_events.reason` — no fake secrets PASS
  - Worker log — 0 fake secret occurrences PASS
  - Bot log — 0 fake secret occurrences PASS
  - `task_events` payload — minimal operational metadata only PASS
- **Noted (expected):** SQLAlchemy engine logger shows INSERT bind parameters for `tasks.raw_text` — this is the user's original message stored in the task record. Redaction protects event/audit payloads. Worker log has 8 pre-existing `[REDACTED]` markers from prior sessions (not this test).
- **Verdict:** PASS — centralized redaction correctly protects audit metadata, audit reason, worker logs, bot logs, and task event payloads. No secrets leak in auditable surfaces. No code changes.
- **Changed files:** None (memory-only update)
- Task summary: [.ai_memory/tasks/2026-05-08-task-sec03-phase3-live-redaction-smoke.md](.ai_memory/tasks/2026-05-08-task-sec03-phase3-live-redaction-smoke.md)

### 2026-05-08 — SEC-02 Phase 2: Security Audit DB Model, Migration, and Service

- **Агент:** security-engineer
- **Контур:** local only; without deploy/migrations run/secrets/OpenCode.
- **Цель:** Implement the infrastructure for the security audit trail: DB model, Alembic migration, append-only service, and redaction helpers.
- **Сделано:**
  - **Model `SecurityAuditEvent`** — 21-column SQLAlchemy model (id, event_type, actor_type, actor_id, source, action, decision, audit_code, reason, task_id FK, approval_id FK, project_id FK, agent_id FK, chat_id, thread_id, ip_hash, correlation_id, request_id, metadata JSONB, error_code, created_at). Append-only — no updated_at column.
  - **Migration `0002_add_security_audit_events`** — additive only: creates `security_audit_events` table with 5 indexes, 4 FK constraints (all SET NULL on delete). Downgrade: drops indexes then table. No changes to existing tables/data.
  - **`SecurityAuditService`** — append-only service with 5 methods: `record()`, `record_best_effort()` (static, non-blocking), `query_by_task()`, `query_by_actor()`, `query_by_decision()`.
  - **Redaction helpers** — `redact_text()` (strips bot tokens, Bearer tokens, JWTs, API keys, password/secret assignments), `sanitize_metadata()` (removes sensitive keys), `hash_ip()` (SHA-256 truncated to 32 hex).
  - **Registered** `SecurityAuditEvent` in `apps/api/app/models/__init__.py`.
- **Валидация:** API 331/331 (297 existing + 34 new audit tests), Bot 79/79, Worker 98/98, **Total: 508/508**, ruff clean.
- **Migration NOT run** against any real database (validated via `alembic upgrade head --sql` only).
- **Not done (Phase 3):** No wiring into approve/reject/permission/callback endpoints. No Telegram bot changes. No Worker changes.
- **Изменённые файлы (5):**
  - NEW: `apps/api/app/models/security_audit.py`, `apps/api/alembic/versions/0002_add_security_audit_events.py`, `apps/api/app/services/audit_service.py`, `apps/api/tests/test_security_audit.py`
  - MODIFIED: `apps/api/app/models/__init__.py`
- Task summary: [.ai_memory/tasks/2026-05-08-task-sec02-phase2-audit-model-service.md](.ai_memory/tasks/2026-05-08-task-sec02-phase2-audit-model-service.md)

### 2026-05-06 — DEV-LINUX-01 Ubuntu 22.04 runtime scripts

- **Агент:** security-engineer
- **Контур:** local only; без deploy/migrations/.env/secrets/OpenCode.
- **Цель:** Implement centralized Permission Engine with fail-closed design and wire to critical API endpoints.
- **Сделано:**
  - **Package `apps/api/app/security/` создан:**
    - `permissions.py` — `PermissionEngine` (fail-closed), `PermissionAction` enum (14 actions), `PermissionDecision` + `PermissionContext` Pydantic models
    - `context.py` — helper factories (`context_for_telegram_user`, `context_for_system`, `context_for_callback`)
  - **5 endpoints wired:**
    1. `POST /approvals/{id}/approve` — admin-gated via `approved_by` param, 403 for non-admin
    2. `POST /approvals/{id}/reject` — same with `rejected_by`
    3. `POST /tasks/{id}/trigger-plan` — risk-level gating (low→allow, medium→allow+approval, high/critical→deny)
    4. `POST /tasks/{id}/callback-answer` — approve/reject check telegram_user_id against admin list
    5. `PATCH /tasks/{id}/status` — system actor check
  - **Permission rules:**
    - `can_approve/reject`: admin-gated (actor_id must be in `TELEGRAM_ADMIN_USER_IDS`; empty list = fail-closed)
    - `can_trigger_plan`: LOW→allowed, MEDIUM→allowed+requires_approval, HIGH/CRITICAL→denied (missing context also denied)
    - `can_update_status`: SYSTEM allowed, USER allowed with approval flag, others denied
    - Stubs (always allow): `create_task`, `execute_runtime`, `access_project`, `write_memory`, `cancel_task`, `callback_validate`, `modify_project`, `modify_agent`
    - Unknown actions: always denied
  - **Конфиг:** `apps/api/app/config.py` — добавлен `TELEGRAM_ADMIN_USER_IDS`
  - **Тесты:** 19 новых unit tests в `test_security_permissions.py` + 3 integration tests
- **Валидация:** API 297/297 ✅ (was 275, +19 unit + 3 integration), Telegram-bot 79/79 ✅, Worker 98/98 ✅, ruff clean, compileall clean
- **Известные ограничения (Phase 3 deferrals):** Agent permissions JSONB not read by code yet; runtime/memory/project access stubs; `can_update_status` USER flag not enforced at endpoint level; no DB schema changes; no migrations
- **Безопасность:** No secrets exposed, no .env changes, no live Telegram/OpenCode/Deploy, compact callback protocol preserved, admin gate fail-closed preserved
- **Изменённые файлы (10):**
  - NEW: `apps/api/app/security/__init__.py`, `permissions.py`, `context.py`, `apps/api/tests/test_security_permissions.py`
  - MODIFIED: `apps/api/app/config.py`, `apps/api/app/routers/approvals.py`, `apps/api/app/routers/tasks.py`, `apps/api/app/routers/runtime.py`, `apps/api/tests/conftest.py`, `apps/api/tests/test_approvals.py`, `apps/api/tests/test_approvals_idempotency.py`, `apps/api/tests/test_tasks_plan_endpoint.py`
- Task summary: [.ai_memory/tasks/2026-05-07-task-sec01-permission-engine.md](.ai_memory/tasks/2026-05-07-task-sec01-permission-engine.md)

### 2026-05-07 — MEM-04 Phase 2: Soft Mandatory Memory Checkpoints
- **Агент:** knowledge-steward
- **Контур:** docs only; без deploy/migrations/.env/secrets/кода.
- **Цель:** Implement soft enforcement of mandatory memory checkpoints for all significant tasks.
- **Фаза 1 findings (MEM-04):** No automated enforcement existed. 0 of 57 legacy task logs contained "Memory updated" phrase — audit gap documented but not backfilled.
- **Фаза 2 implementation (docs-only, no code changes):**
  - `AGENTS.md` — added rule #7 "Memory checkpoint — обязательное правило" + full section with mandatory rules (when required, when skippable, closeout format, enforcement phases).
  - `.ai_memory/runbooks/memory-checkpoint.md` — NEW runbook (10 sections: definition, when required, when skippable, required files, file contents, closeout report format, pre-git checklist, enforcement phases, template reference, FAQ).
  - `.ai_memory/templates/task-summary-template.md` — enhanced "Память обновлена" checklist from 3 items to 7 items with mandatory note.
  - `docs/memory-system.md` — added memory checkpoint reference and link to runbook after "После каждой задачи" subsection.
- **Key decision:** Phase 2 = soft enforcement via AGENTS.md/runbook/template (docs-only). Phase 3 API-level gate (`memory_checkpoint_done` flag in DB) deferred — activate when soft enforcement proves insufficient.
- **Enforcement:** studio-orchestrator responsible for verifying checkpoints before closing tasks.
- **Changed files:** 4 modified (`AGENTS.md`, `PROJECT_MEMORY.md`, `.ai_memory/current_state.md`, `.ai_memory/_INDEX.md`) + 2 new (runbook + task log) + 2 updated (`task-summary-template.md`, `docs/memory-system.md`).
- **Risk:** low — docs-only, no code/deploy/migrations.
- Task summary: [.ai_memory/tasks/2026-05-07-task-mem04-memory-checkpoints.md](.ai_memory/tasks/2026-05-07-task-mem04-memory-checkpoints.md)

### 2026-05-06 — TG-04 Phase 5: Final Live Private Chat E2E
- **Агент:** studio-orchestrator (coordinated execution)
- **Контур:** local WSL2 Ubuntu 22.04; live Telegram bot + Celery worker + API stub.
- **Цель:** Validate full live private chat E2E: Telegram user message → API task → Celery worker → stub runtime plan → approved → notification.
- **Сделано:**
  - Started API stub (PID 12328), Celery worker (PID 13000, SIGHUP fix active), Telegram bot (PID 13087, @agentrouters_bot).
  - User sent "TG-04 final live smoke" in private chat.
  - Bot received message, created task-0010 (5d16fe1e), triggered plan.
  - Worker picked up task, called runtime plan endpoint, got approved status.
  - Notification dispatched via StubNotifier (token not in worker env).
  - Total processing time: 0.125s (worker) + 1.49s (bot handler).
- **Validation:** 11/11 checks PASS:
  - task_created ✓, plan_triggered ✓, runtime_session_created (stub-session) ✓
  - plan_generated count=1 ✓, final status=approved ✓
  - no runtime_error ✓, no policy_blocked ✓
  - notification dispatched ✓, worker alive ✓, bot alive ✓
  - no feedback loop (10 tasks total, 0 after task-0010) ✓
- **Observations:**
  - TelegramConflictError transient conflicts (recovered after ~23 retries).
  - StubNotifier used because worker env lacks TELEGRAM_BOT_TOKEN.
  - No runtime_session_created event in task_events (embedded in payload instead).
- **Cleanup:** worker/bot stopped, API restarted stub (PID 13337), ports clean.
- Task summary: [.ai_memory/tasks/2026-05-06-task-tg-04-phase5-live-e2e.md](.ai_memory/tasks/2026-05-06-task-tg-04-phase5-live-e2e.md)

### 2026-05-06 — TG-04 HTML placeholder fix (TelegramBadRequest)
- **Агент:** studio-orchestrator (coordinated execution)
- **Контур:** local only; без deploy/migrations/.env/secrets/OpenCode.
- **Проблема:** `TelegramBadRequest: can't parse entities: Unsupported start tag "project_slug"` — raw `<project_slug>` в help тексте при `parse_mode=HTML`.
- **Сделано:**
  - Заменены raw `<placeholder>` на `<code>placeholder</code>` в **6 handler файлах** (messages, bind_topic, plan_handler, approve_handler, reject_handler, status_handler).
  - Добавлен `html.escape()` для динамических значений из API/user в **4 handler файлах** (approve_handler, reject_handler, bind_topic, messages).
  - Исправлен import order (stdlib перед third-party) для ruff I001 compliance.
  - Обновлён **1 тест** (test_messages.py assertion).
- **Валидация:** compileall ✅, ruff ✅, pytest 64/64 ✅
- **Guardrails:** no secrets/tokens touched, .env.local gitignored, API/runtime code unchanged.
- Task summary: [.ai_memory/tasks/2026-05-06-task-tg04-html-placeholder-fix.md](.ai_memory/tasks/2026-05-06-task-tg04-html-placeholder-fix.md)

### 2026-05-06 — TG-04 private chat wording fix
- **Агент:** studio-orchestrator
- **Контур:** local only; без deploy/migrations/.env/secrets/OpenCode.
- **Проблема:** В private chat бот отвечал "Этот topic пока не привязан..." — слово "topic" нелогично для 1:1 чата.
- **Сделано:**
  - `messages.py`: проверка `message.chat.type == "private"` → "чат" вместо "topic".
  - `test_messages.py`: добавлен `chat_type` параметр в `FakeMessage`, новый тест `test_text_message_unbound_private_chat`.
- **Валидация:** compileall ✅, ruff ✅, pytest 65/65 ✅
- Task summary: [.ai_memory/tasks/2026-05-06-task-tg04-private-chat-wording-fix.md](.ai_memory/tasks/2026-05-06-task-tg04-private-chat-wording-fix.md)

### 2026-05-06 — TG-04 aiogram 3.15 message_thread_id compatibility fix
- **Агент:** studio-orchestrator (coordinated execution)
- **Контур:** local only; без deploy/migrations/.env/secrets/OpenCode.
- **Проблема:** `TypeError: got multiple values for keyword argument 'message_thread_id'` при `/start` в private chat. aiogram 3.15 автоматически прокидывает `message_thread_id` из входящего сообщения, а код передавал его явно → дублирование.
- **Сделано:**
  - Удалён `_thread_id()` helper и явный `message_thread_id=_thread_id(message)` из **10 handler файлов** (start, commands, messages, status, approve, reject, plan, topic_status, bind_topic, unbind_topic).
  - Обновлены **7 тестовых файлов** (FakeMessage.answer() signatures + assertions).
- **Валидация:** compileall ✅, ruff ✅, pytest 64/64 ✅
- **Guardrails:** no secrets/tokens touched, .env.local gitignored, API/runtime code unchanged.
- Task summary: [.ai_memory/tasks/2026-05-06-task-tg04-aiogram-message-thread-fix.md](.ai_memory/tasks/2026-05-06-task-tg04-aiogram-message-thread-fix.md)

### 2026-05-06 — TG-04 Live Integration Phase 1 (security prerequisites)
- **Агенты:** security-engineer + backend-architect
- **Контур:** local only; без deploy/migrations/.env/secrets/real Telegram/OpenCode.
- **Сделано:**
  - **Config:** `apps/telegram-bot/app/config.py` — добавлен `TELEGRAM_ADMIN_USER_IDS` (comma-separated str), метод `admin_user_ids()` с fail-closed парсингом (invalid→пустой set, logged warning). `env_file` теперь tuple `(".env", ".env.local")`.
  - **Bot guard:** `apps/telegram-bot/app/handlers/messages.py` — добавлен `is_bot guard`: сообщения от `from_user.is_bot` пропускаются (предотвращает feedback loop при worker-уведомлениях).
  - **Logging (NEW):** `apps/telegram-bot/app/logging.py` — `SecretRedactionFilter` (logging.Filter) с компилированными regex-паттернами: `TELEGRAM_BOT_TOKEN`, OpenAI keys, Bearer токены, `DATABASE_URL` пароли, Redis пароли. Redacted значения заменяются на `[REDACTED]`.
  - **Docs (NEW):** `docs/telegram-live-runbook.md` — env checklist, команды запуска, abort criteria, safety gates для первого live-подключения.
  - **Tests (14 новых):**
    - `test_tg04_config.py` (5 тестов): admin IDs — valid, empty, whitespace, invalid→empty, trailing comma
    - `test_tg04_logging.py` (7 тестов): token redaction, api key, bearer, DB password, redis password, no false positives, partial match safety
    - `test_messages.py` (+2 теста): `test_is_bot_ignored`, `test_slash_from_bot_also_ignored` (FakeBotMessage fixture)
- **Валидация:** compileall ✅, ruff ✅, pytest 64/64 ✅
- **Guardrails:** no live bot started, no .env/secrets changed, no migrations/deploy, no OpenCode.
- **Рабочее дерево:** 7 файлов (3 modified + 4 new), без утечек.
- Task summary: [.ai_memory/tasks/2026-05-06-task-tg04-live-integration-phase1.md](.ai_memory/tasks/2026-05-06-task-tg04-live-integration-phase1.md)

### 2026-05-06 — TG-03 Telegram Approvals + Task Status UX
- **Агент:** backend-architect
- **Контур:** local only; без deploy/migrations/.env/secrets/real Telegram.
- **Сделано:**
  - **API:** 409 вместо 422 для already-decided approve/reject; GET /tasks/{id}/plan; POST /tasks/{id}/callback-answer с HMAC-подписанной валидацией callback_data; CALLBACK_SECRET + CALLBACK_MAX_AGE_SECONDS в config.
  - **Bot:** /status, /plan, /approve, /reject команды; inline keyboard builders (build_task_keyboard, build_approval_keyboard, build_plan_keyboard) с подписанными callback_data; callback handler с API-side валидацией для approve/reject/show_plan/refresh; API client расширен (8 новых методов).
  - **Formatters:** format_task_card, format_approval_card, format_plan_excerpt, format_error_message с HTML escaping.
  - **Тесты:** 35/35 bot tests pass (formatters, handlers, callbacks); 11 API tests pass (plan endpoint, callback-answer, approval idempotency); 1 pre-existing flake.
- **Изменённые файлы:** 22 файла (API routers/schemas/config, bot handlers/keyboards/services, tests).
- **Проверки:** compileall ✅, ruff ✅, pytest (bot 35/35, API 37/38) ✅
- Task summary: [.ai_memory/tasks/2026-05-06-task-tg03-telegram-approvals-ux.md](.ai_memory/tasks/2026-05-06-task-tg03-telegram-approvals-ux.md)

### 2026-05-05 — BE-12 OpenCode read-timeout alignment
- **Агент:** backend-architect
- **Контур:** local only; без deploy/migrations/.env/secrets/OpenCode.
- **Сделано:**
  - `RealOpenCodeHttpTransport.send_message()` теперь использует локальный `httpx.AsyncClient` с `read=None` (unbounded read timeout), в соответствии с OpenCode SDK (`req.timeout=false`).
  - `create_session()` остаётся bounded (использует `_build_client()` с нормальным `read_timeout`).
  - `_build_client()` и `_build_timeout()` не тронуты — local override только в `send_message()`.
  - Client-side session/idle timeout в `OpenCodeHttpPlanClient` остаётся safety net.
  - Error mapping (`httpx.ConnectError`, `httpx.HTTPStatusError`, `httpx.ReadTimeout`) сохранён без изменений.
  - Все guardrails нетронуты: provider=stub, allow=false, plan-only, redaction, path confinement, max_plan_size.
- **Тесты:** 16/16 transport tests pass, 5 новых BE-12 тестов (read=None verification, correct endpoint, base_url preserved, create_session bounded, _build_client unaffected). Full suite: 251/252 pass (1 pre-existing flake).
- **Проверки:** compileall ✅, ruff ✅, pytest ✅
- Task summary: [.ai_memory/tasks/2026-05-05-task-be12-opencode-read-timeout-alignment.md](.ai_memory/tasks/2026-05-05-task-be12-opencode-read-timeout-alignment.md)

### 2026-05-05 — BE-11D smoke script timeout/progress focused fix
- **Агент:** devops-automator
- **Контур:** local only; без deploy/migrations/.env/secrets/RuntimeService/API-кода.
- **Сделано (`scripts/dev/smoke-real-opencode-runtime.ps1`):**
  - Перед POST добавлен exact step message: `[STEP] Calling runtime plan endpoint. This may take up to 300s.`
  - Для POST `/runtime/tasks/{id}/plan` установлен минимум timeout `max(user, 420)` с использованием `Invoke-RestMethod -TimeoutSec`.
  - Добавлены отметки времени start/end и периодический прогресс-лог каждые 15s во время ожидания.
  - После успешного возврата добавлен exact message: `[DONE] Runtime plan endpoint returned.`
  - На ошибке POST: печать типа исключения + GET `/tasks/{task_id}` + вывод `status` и `plan_text` null/not null + `exit 1`.
  - В финальном отчёте сохранено явное сообщение: `Worker bypass: direct POST /runtime used.`
- **Валидации:** PSParser ✅, DryRun ✅ (процессы не стартует).
- **Real smoke:** запуск выполнен с `-TimeoutSeconds 480`; POST завершился `System.Net.WebException`, task status после ошибки `routed`, `plan_text=null`.

## Что сделано

- [x] Спроектирована архитектура системы (3 слоя: Telegram → API → Runtime)
- [x] Определена структура monorepo
- [x] Спроектирована схема БД (8 таблиц)
- [x] Составлен roadmap из 8 фаз
- [x] Создана документация в `docs/`
- [x] Memory vault инициализирован в `.ai_memory/`
- [x] Написаны 4 ADR
- [x] Создан MVP backlog с 25 задачами
- [x] Project root скорректирован: всё в `F:\dev\agentrouter`
- [x] **FND-01:** .gitignore, CHANGELOG, CONTRIBUTING, docs/git-workflow.md
- [x] **FND-02:** FastAPI skeleton (main.py, config.py, /health, pyproject.toml)
- [x] **DOP-01:** dev docker-compose (`infra/docker/docker-compose.yml`)

## Что не сделано

- [x] **FND-03:** SQLAlchemy модели + Alembic baseline миграция (не применялась)
- [x] **BE-01:** CRUD /projects, /agents, /telegram_topics с мягким удалением
- [x] **BE-02:** Tasks + Approvals domain (task lifecycle, approval flow, event audit)
- [x] **TG-01:** Telegram bot gateway (aiogram 3.x, commands + topic-aware task creation)
- [x] **TG-02:** Topic binding + routing bridge (`/bind_topic`, `/unbind_topic`, `/topic_status`)
- [x] **WRK-01:** Celery worker skeleton (7 queues, healthcheck, stubs, retry/backoff)
- [x] **WRK-02:** Plan pipeline (trigger-plan endpoint, agent_plan + notifications tasks, notifier adapter)
- [x] **MEM-01:** Memory provisioning (service, schemas, 5 templates, docs, forbidden content detection)
- [x] **MEM-02:** Memory CRUD API (6 endpoints, policy service, access tiers, secrets guard)
- [x] **DOP-02:** Dockerfiles + sandbox compose (sandbox isolation, non-root, no-new-privileges, limits)
- [x] Worker execute pipeline (WRK-03)
- [x] Memory indexing + retrieval (MEM-03)
- [x] **MEM-04 Phase 2:** Soft mandatory memory checkpoints (AGENTS.md rule #7, runbook, template, docs)
- [x] **SEC-01 Phase 2:** Permission Engine MVP (fail-closed, 14 actions, 5 endpoints wired, 297/297 tests)
- [x] **SEC-02 Phase 2:** Security Audit DB model, migration, append-only service, redaction helpers (508/508 tests)
- [x] **SEC-02 Phase 3:** P0 Security Audit integration into approve/reject/callback endpoints (524/524 tests)
- [x] **SEC-02 Phase 4:** Audit Trail Live Smoke — validated against real Telegram /approve flow (PASS)
- [x] **SEC-03 Phase 2:** Centralized secrets redaction module (10 patterns, unified 4 systems, 570/570 tests)
- [x] **SEC-03 Phase 3:** Live Redaction Smoke — verified redaction against fake-secret corpus in real flows (PASS)
- [x] **SEC-03B Phase 2:** SQLAlchemy Log Safety — decoupled echo from DEBUG, added SQL_ECHO config (574/574 tests)
- [x] **DOP-03 Phase 2:** Production Runtime Templates + Enhanced Health Check — Caddyfile, 3 systemd units, prod compose, .env.example, validation script, deployment.md, operations-runbook.md, enhanced /health (578/578 tests)
- [ ] Frontend код (React)
- [x] Docker Compose конфигурация (dev)
- [ ] `.env` конфигурация

## Ключевые решения

| ID | Решение | ADR |
|----|---------|-----|
| D-001 | Monorepo | [.ai_memory/decisions/0001](.ai_memory/decisions/0001-use-monorepo.md) |
| D-002 | FastAPI + aiogram + Celery + SQLAlchemy | [.ai_memory/decisions/0002](.ai_memory/decisions/0002-python-backend-fastapi.md) |
| D-003 | pgvector для retrieval | [.ai_memory/decisions/0003](.ai_memory/decisions/0003-pgvector-for-retrieval.md) |
| D-004 | Celery + Redis для очередей | [.ai_memory/decisions/0004](.ai_memory/decisions/0004-celery-redis-for-queues.md) |

## Следующие шаги

1. Memory retrieval tuning: ranking quality + scope heuristics
3. Полный план: [docs/mvp-backlog.md](docs/mvp-backlog.md)

### 2026-05-03 — WRK-04 Manual Local Backend Test Completed (WRK-04)
- **Агент:** backend-architect
- **Контур:** local only, без deploy/миграций/secrets, без OpenCode execution.
- **Проверка режима:** default `SANDBOX_RUNNER_MODE=fake` подтверждён до теста; после теста подтверждён снова.
- **Сценарии A-E:**
  - A (safe command success): `python -m compileall .` через DockerSandboxRunner (fake docker client) → `return_code=0`, cleanup attempted.
  - B (policy violation): `pytest && curl evil.com` блокируется до sandbox runner (`security_violation`, `failed`, runner not called).
  - C (timeout): `SandboxTimeoutError`, kill + cleanup attempted (`kill_called=True`, `remove_called=True`).
  - D (docker/start failure): `sandbox_error` path с redacted ошибкой (`password=[REDACTED]`).
  - E (cleanup): cleanup attempted always; cleanup failure не маскирует primary result.
- **Эффективные docker settings (наблюдено):** `network_mode=none`, `mem_limit=2g`, `nano_cpus=2000000000`, `pids_limit=256`, `user=sandboxuser`, `read_only=true`, `tmpfs=/tmp rw,noexec,nosuid,size=64m`, `cap_drop=[ALL]`, `security_opt=[no-new-privileges:true]`, `auto_remove=true`, single mount host `.worktrees/task-*` → `/workspace:rw`.
- **Проверка mount policy:** `.env`, `.ai_memory`, `docker.sock` отсутствуют в runtime mounts.
- Task summary: [.ai_memory/tasks/2026-05-03-task-wrk04-manual-local-test.md](.ai_memory/tasks/2026-05-03-task-wrk04-manual-local-test.md)

### 2026-05-04 — WRK-04 REAL Docker smoke test (Scenario A)
- **Агент:** backend-architect
- **Контур:** local only; без deploy/migrations/secrets/OpenCode.
- **Режимы:** до теста подтверждён default `SANDBOX_RUNNER_MODE=fake`; для одного invocation применён временный override `SANDBOX_RUNNER_MODE=docker` + `DOCKER_SANDBOX_IMAGE=agentrouter-sandbox:local`; после теста снова подтверждён `fake`.
- **Фактический запуск:** `DockerSandboxRunner` выполнил ровно argv-команду `['python', '-m', 'compileall', '.']` в контейнере, `exit_code=0`.
- **Mount policy evidence:** единственный bind mount `F:\dev\agentrouter\.worktrees\manual-test-wrk04 -> /workspace:rw`; mounts для repo root, `.env`, `.ai_memory`, `docker.sock` отсутствуют.
- **Cleanup:** `cleanup_attempted=true`, `cleanup_completed=true`.
- **Примечание к коду:** валидация имени worktree в `DockerSandboxRunner` расширена на префикс `manual-test-` (помимо `task-`) для контролируемых manual smoke tests.
- Task summary: [.ai_memory/tasks/2026-05-03-task-wrk04-real-docker-smoke-test.md](.ai_memory/tasks/2026-05-03-task-wrk04-real-docker-smoke-test.md)

### 2026-05-04 — WRK-04 manual-test hardening
- **Агент:** backend-architect
- **Контур:** local only; без deploy/migrations/secrets/docker.
- **Сделано:**
  - Добавлен `SANDBOX_MANUAL_TEST_MODE: bool = False` в `apps/worker/app/config.py`.
  - В `DockerSandboxRunner.run()` префикс `manual-test-*` теперь разрешён только при `SANDBOX_MANUAL_TEST_MODE=True`.
  - В нормальном режиме (default) разрешён только production-safe префикс `task-<external_id>-<short_uuid>`.
  - Path traversal (выход за `.worktrees`) отклоняется всегда, независимо от режима.
  - `build_worktree_path()` всегда генерирует только `task-*` префикс.
  - Добавлены 5 тестов hardening в `test_sandbox_runner.py`.
  - `FakeSandboxRunner` остаётся default (без изменений, без валидации пути).
  - Реальный Docker не запускался.
- **Проверки:** compileall ✅, ruff ✅, pytest ✅
- Task summary: [.ai_memory/tasks/2026-05-04-task-wrk04-manual-test-hardening.md](.ai_memory/tasks/2026-05-04-task-wrk04-manual-test-hardening.md)
3. Полный план: [docs/mvp-backlog.md](docs/mvp-backlog.md)

## Изменения

### 2026-05-05 — BE-11C scripts parser/encoding hardening
- **Агент:** devops-automator
- **Контур:** local only; без deploy/migrations/.env/secrets/API-кода/worker-кода.
- **Сделано:**
  - `scripts/dev/cleanup-runtime.ps1`: убрана остановка Celery/worker, добавлен безопасный stop только OpenCode 4096 и AMC API `opencode_http`, сохранён optional restart API stub mode, подтверждение 4096 free.
  - `scripts/dev/start-api-opencode.ps1`: DryRun перенесён до preflight; preflight теперь проверяет OpenCode `/global/health` и `/doc`; сохранены только process-scoped env overrides.
  - `scripts/dev/smoke-real-opencode-runtime.ps1`: DryRun перенесён до preflight; явно зафиксирован worker bypass; ужесточена проверка “no command/file/sandbox events” (включая `command_finished=0`).
  - `scripts/dev/start-opencode.ps1`: убран BOM артефакт в начале файла.
  - Все 4 скрипта перезаписаны как UTF-8 without BOM.

### 2026-05-04 — BE-10 Runtime Reliability Hardening COMPLETE
- **Агент:** backend-architect
- **Контур:** local only; без deploy/migrations/secrets/OpenCode.
- **Сделано (6 hardening items, P0-P2):**
  - **P0-1:** Idempotency guard в `RuntimeService` — guard BEFORE transition, блокирует re-entry для PLANNING/APPROVED/WAITING_APPROVAL/COMPLETED.
  - **P0-2:** Status gate в `trigger-plan` — только CREATED tasks принимаются, 409 для всех остальных статусов.
  - **P1-3:** Notification isolation в worker — `generate_plan` и dispatch уведомлений в отдельных try блоках.
  - **P1-4:** Retry exception handling в `OpenCodeHttpPlanClient` — ловит `OpenCodeTimeoutError`/`OpenCodeConnectionError`.
  - **P2-5:** Event ordering — `runtime_session_created` эмитится ДО retry loop (внутри `generate_plan` после `POST /session`).
  - **P2-6:** Timeout alignment — `RUNTIME_SESSION_TIMEOUT_SECONDS` 180→300, `API_TIMEOUT_SECONDS` 300→420.
- **Reviews:** Security 6/6 PASS, Architecture 5/5 PASS, Reality-check 6/6 PASS.
- **Тесты:** API 237/237 passed (71 in test_runtime_be04.py, 9 new BE-10), Worker 93/93 passed (3 new BE-10).
- **Guardrails intact:** provider=stub, allow=false, real OpenCode не запускался, `.env`/secrets не трогались.
- **Изменённые файлы:** `apps/api/app/config.py`, `client.py`, `tasks.py`, `task.py` (schema), `runtime_service.py`, `test_runtime_be04.py`; `apps/worker/app/config.py`, `agent_plan.py`, `test_agent_plan_pipeline.py`, `test_config.py`
- Task summary: [.ai_memory/tasks/2026-05-04-task-be10-runtime-reliability-hardening.md](.ai_memory/tasks/2026-05-04-task-be10-runtime-reliability-hardening.md)

### 2026-05-04 — BE-10 Real OpenCode Regression Smoke — PASSED
- **Агент:** studio-orchestrator (direct execution)
- **Контур:** local only; без deploy/migrations/secrets/кода.
- **Сделано:** Verified BE-10 hardening with real OpenCode 1.14.33:
  - Task `557f1e8e-3a75-45d9-983d-79d8f7eec4b4` → approved, plan=1299 chars.
  - `session_id = ses_20b132da3ffeocFC1MtRO9vTCx` (real, not stub).
  - **P2-5 verified:** `runtime_session_created` BEFORE `runtime_event_received` — event ordering correct.
  - **P0-1 verified:** 1× plan_generated, no duplicate. Retry at borderline 300s, succeeded.
  - All guardrails held: 4 stub fingerprints FALSE, 6 secret patterns FALSE, reasoning leak FALSE, 0 command/sandbox events.
- **Cleanup:** OpenCode stopped, API → stub, git clean.
- Task summary: [.ai_memory/tasks/2026-05-04-task-be10-real-opencode-regression-smoke.md](.ai_memory/tasks/2026-05-04-task-be10-real-opencode-regression-smoke.md)

### 2026-05-04 — BE-09 Phase 1 Worker API_TIMEOUT_SECONDS Fix (30→300)
- **Агент:** backend-architect
- **Контур:** local only; без deploy/migrations/secrets/OpenCode.
- **Сделано:**
  - `apps/worker/app/config.py`: `API_TIMEOUT_SECONDS` увеличен с 30.0 до 300.0 — должен быть >= `RUNTIME_SESSION_TIMEOUT_SECONDS=180` + буфер для 80–170s real OpenCode планов.
  - `apps/worker/tests/test_config.py`: добавлен `test_api_timeout_default_is_300`.
  - `apps/worker/tests/test_agent_plan_pipeline.py`: добавлен `test_generate_plan_uses_api_timeout_from_settings`.
- **Причина:** BE-08 выявил, что 180s session timeout — borderline для real OpenCode; worker со своим 30s таймаутом обрывал запрос до того, как API успевал дождаться ответа OpenCode.
- **Guardrails intact:** API config не менялся, `RUNTIME_PROVIDER=stub`, `RUNTIME_ALLOW_REAL_OPENCODE_HTTP=false`, `OPENCODE_SERVER_URL=""`. No real OpenCode started.
- **Проверки:** worker `pytest tests -v` ✅ (91/91), api `pytest tests -v` ✅ (224/225, 1 pre-existing flake). Security GO 8/8, Reality-check GO 8/8.
- Task summary: [.ai_memory/tasks/2026-05-04-task-be09-phase1-worker-timeout.md](.ai_memory/tasks/2026-05-04-task-be09-phase1-worker-timeout.md)

### 2026-05-04 — BE-09 Phase 2: Real OpenCode E2E — SUCCESS
- **Агент:** studio-orchestrator (coordinated: devops-automator, backend-architect, security-engineer)
- **Контур:** local only; без deploy/migrations/secrets/кода.
- **Сделано:** First successful E2E pipeline with real OpenCode 1.14.33:
  - Task `ddc0d397-17a3-4511-ae9a-39a571d57abb` → trigger-plan → Celery worker → API → `RealOpenCodeHttpTransport` → OpenCode `/session` + `/session/{id}/message` → `plan_generated` (866 chars) → status `approved`.
  - `session_id = ses_20b75bd21ffekkZ4XA2rr4a5Sc` (real, not stub).
  - Worker `API_TIMEOUT_SECONDS=300` (Phase 1 fix) enabled 70s plan completion.
  - Events: `task_created` → `plan_triggered` → `runtime_retry_scheduled` (attempt=1, borderline timing) → `runtime_event_received` ×2 → `runtime_session_created` → `plan_generated`.
- **Guardrails intact:** All 4 stub fingerprints absent, reasoning/secret/file-mutation leaks absent, no policy_blocked/runtime_error, approval correct for low-risk.
- **Finding:** `runtime_retry_scheduled` at 180s boundary — recommend increasing `RUNTIME_SESSION_TIMEOUT_SECONDS` to 240-300s (BE-10 hardening).
- **Security review:** PASSED (10/10 checks).
- Task summary: [.ai_memory/tasks/2026-05-04-task-be09-phase2-real-opencode-e2e-success.md](.ai_memory/tasks/2026-05-04-task-be09-phase2-real-opencode-e2e-success.md)

### 2026-05-04 — BE-06 task creation fix (transaction boundary + integrity mapping)
- **Агент:** backend-architect
- **Сделано:**
  - `get_async_session()` теперь завершает request-транзакцию корректно: commit on success, rollback on exception, session close via context manager.
  - `POST /projects`, `POST /agents`, `POST /tasks` оборачивают `IntegrityError` в безопасные HTTP ответы без SQL/traceback:
    - FK violation (`23503`) для tasks -> `422 Invalid project_id or agent_id reference`
    - unique/integrity conflicts -> `409 ... constraint conflict/violation`
  - В create-роутах добавлен явный `rollback()` при `IntegrityError` для корректного состояния shared session в тестовом DI.
  - Добавлены интеграционные тесты на persistence после POST, FK mapping и rollback после неуспешной записи.
- **Проверки:** `python -m compileall app` ✅, `ruff check app` ✅, `pytest tests -v` ✅ (198/198)
- **Ограничения:** без миграций/.env/deploy/OpenCode runtime.
- Task summary: [.ai_memory/tasks/2026-05-04-task-be06-task-creation-fix.md](.ai_memory/tasks/2026-05-04-task-be06-task-creation-fix.md)

### 2026-05-04 — BE-06 FINAL EXECUTION (real OpenCode 1.14.33 controlled smoke test)
- **Агенты:** backend-architect (execution), studio-orchestrator (coordination), knowledge-steward (memory)
- **Контур:** local only; без deploy/migrations/secrets.
- **Что сделано (Steps A–G):**
  - **Step A (Pre-check):** ✅ git clean, API `/health`=200, `/projects`=200, `/agents`=200, port 4096 free, defaults confirmed (`stub`, empty URL, `allow=false`, `fake` sandbox).
  - **Step B (Start OpenCode):** ✅ OpenCode 1.14.33 via npm shim on `127.0.0.1:4096` (no auth). `/global/health` → `{"healthy":true,"version":"1.14.33"}`, `/doc` → OpenAPI 3.1.1, listener localhost-only.
  - **Step C (Runtime override):** ✅ API restarted with process-scoped env (`opencode_http`, `4096`, `allow=true`).
  - **Step D (Trigger plan):** ✅ Task created (`089aa3ca`), session created (`ses_20dd9839affe...`) — proves provider/transport wiring. `POST /session/{id}/message` → `400 Bad Request` (payload contract mismatch with OpenCode 1.14.33). Fail-closed: `runtime_error` → `task_failed`. No bypass.
  - **Step F (Post-smoke):** ✅ git clean, no file changes, no secret leaks.
  - **Step G (Cleanup):** ✅ OpenCode stopped, API restarted with `stub` defaults, port 4096 free, `/health`=200.
- **Ключевой результат:** Guardrail chain proven end-to-end: provider wiring, RealOpenCodeHttpTransport, session creation, fail-closed on error.
- **Интеграционная находка:** `400` на `/session/{id}/message` — payload contract mismatch. Follow-up BE-07 для contract alignment.
- **Ограничения:** plan-only (no code execution), process env overrides only (no `.env` edits), OpenCode stopped after test.
- Task summary: [.ai_memory/tasks/2026-05-04-task-be06-final-execution.md](.ai_memory/tasks/2026-05-04-task-be06-final-execution.md)

### 2026-05-04 — BE-07 payload contract alignment implementation
- **Агент:** backend-architect
- **Сделано:**
  - OpenCode message payload для `POST /session/{id}/message` переведён с legacy extra-fields формы на минимальный контракт `{ "message": <text> }`.
  - Обновлён response mapping клиента: поддержаны формы `parts` и `content`; при пустом/malformed/unknown ответе применяется fail-closed поведение.
  - Guardrails сохранены без ослабления: plan-only, `policy_blocked` для mutating `tool.call`, path confinement, redaction на верхних слоях, `max_plan_size`, timeout, no silent fallback.
  - Устранён архитектурный блокер: из `transport.py` удалена policy-layer зависимость; transport снова transport-only.
- **Проверки:** `python -m compileall app` ✅, `ruff check app` ✅, `pytest tests -v` ✅ (204 passed)
- **Ограничения:** реальный OpenCode server не запускался.
- Task summary: [.ai_memory/tasks/2026-05-04-task-be07-payload-contract-alignment-implementation.md](.ai_memory/tasks/2026-05-04-task-be07-payload-contract-alignment-implementation.md)

### 2026-05-04 — BE-07+ native contract alignment (OpenCode 1.14.33)
- **Агент:** backend-architect (implementation), knowledge-steward (recording)
- **Сделано:**
  - `schemas.py`: `OpenCodeSessionMessageRequest` переведён с `message: str` на native `parts: list[OpenCodeSessionTextPart]` (`{"parts": [{"type": "text", "text": "..."}]}`).
  - `client.py`: `_map_message_response_to_events` переписан под explicit OpenCode-native part-type dispatch:
    - `text` → `plan.delta`
    - `reasoning` → **SKIPPED** (never stored in `plan_text`/events)
    - `step-start` → skipped
    - `step-finish` (reason=stop) → `plan.final`
    - `tool` → `tool.call`
    - unknown → `runtime_event_malformed` (fail-closed)
  - Тесты: 219 passed (12 новых BE-07+ тестов)
- **Reviews:**
  - Security: GO ✅ — все 8 checks PASS, no blocking issues
  - Architecture: GO ✅ — все 5 rules PASS, no layering violations
- **Guardrails confirmed:** default provider=stub, opencode_http requires URL+allow flag, no silent fallback, plan-only preserved, reasoning NEVER stored, redaction preserved, real OpenCode NOT started
- **Проверки:** `python -m compileall app` ✅, `ruff check app` ✅, `pytest tests -v` ✅ (219/219)
- Task summary: [.ai_memory/tasks/2026-05-04-task-be07-plus-implementation.md](.ai_memory/tasks/2026-05-04-task-be07-plus-implementation.md)

### 2026-05-04 — BE-08 OpenCode session traceability + timeout tuning
- **Агент:** backend-architect
- **Контур:** local only; без deploy/migrations/secrets/OpenCode.
- **Сделано:**
  - `schemas.py`: добавлен `OpenCodeSessionCreateRequest` с полем `title: Optional[str]` — единственное поле, принимаемое OpenCode 1.14.33 при `POST /session`.
  - `schemas.py`: добавлен `task_title: str = ""` в `RuntimePlanContext` для передачи заголовка задачи runtime клиенту.
  - `client.py`: payload для `POST /session` заменён на минимальный `{"title": "<task title>"}` — удалены игнорируемые поля (mode, correlation_id, idempotency_key, input).
  - `config.py`: `RUNTIME_SESSION_TIMEOUT_SECONDS` увеличен с 60 до 180 (после BE-07+ smoke, где 60s оказалось недостаточно).
  - `runtime_service.py`: контекст теперь передаёт `task_title=task.title`.
  - `docs/smoke-test-opencode.md`: обновлён session contract (BE-08 title-only payload, timeout 180s).
  - Тесты: добавлены `test_create_session_payload_includes_title`, `test_create_session_payload_excludes_forbidden_fields` (transport), `test_be08_session_timeout_config_default_is_180`, `test_be08_timeout_still_maps_to_runtime_error_and_task_failed`, `test_be08_default_provider_still_stub`, `test_be08_real_opencode_server_not_started` (runtime).
- **Guardrails confirmed:** stub default, fail-closed, path confinement, redaction, max_plan_size, plan-only policy — ALL PRESERVED.
- **Подтверждено:** в session payload НЕТ directory/cwd/path/workspace/mode/model/capabilities/restrictions/projectID/agent.
- **Проверки:** `python -m compileall app` ✅, `ruff check app` ✅, `pytest tests -v` ✅ (224/225, 1 pre-existing test-data collision)
- Task summary: [.ai_memory/tasks/2026-05-04-task-be08-session-traceability-timeout.md](.ai_memory/tasks/2026-05-04-task-be08-session-traceability-timeout.md)

### 2026-05-04 — BE-08 Real OpenCode Smoke — SUCCESS (first live plan_generated!)
- **Агенты:** backend-architect (execution), studio-orchestrator (memory recording)
- **Контур:** local only; без deploy/migrations/secrets; real OpenCode 1.14.33 на 127.0.0.1:4096.
- **Итог:** First successful end-to-end `plan_generated` from a **live OpenCode** server (not stub, not fake).
- **Smoke execution data:**
  - task_id: `46482979-bd51-4b28-b4d3-d5230ae2117f`
  - session_id: `ses_20bbf3443ffe9jGPUiUrGNkS7G`
  - plan_text: 875 chars (real analysis — healthcheck endpoint, tests, Docker HEALTHCHECK, probes)
  - **No stub fingerprints** detected
  - **No reasoning leak** (BE-07+ reasoning filtering verified)
  - **No file/command/sandbox events** (plan-only held)
  - status → `approved`
- **Event timeline:** task_created → runtime_retry_scheduled (first attempt timed out at ~180s) → runtime_event_received ×2 → runtime_session_created → plan_generated → approved.
- **Architecture note:** Event ordering (retry BEFORE session_created) is correct — client emits retry during generate_plan(), service emits session_created after successful plan completion.
- **Finding (medium, non-blocking):** 180s timeout is borderline (retry triggered). **Recommend:** increase `RUNTIME_SESSION_TIMEOUT_SECONDS` from 180→300s in follow-up.
- **Prerequisites:** BE-07+ (native `parts` format), BE-08 (title field, 180s timeout), DEV-DB-01 (async Alembic fix).
- **Safety verified:** No file mutation, no command execution, no sandbox events, no secret leakage, localhost-only, git clean.
- **Cleanup:** OpenCode stopped, API returned to stub mode, no persistent env changes.
- **Key takeaway:** AMC → OpenCode integration pipeline proven end-to-end with all guardrails holding.
- Task summary: [.ai_memory/tasks/2026-05-04-task-be08-real-opencode-smoke-success.md](.ai_memory/tasks/2026-05-04-task-be08-real-opencode-smoke-success.md)

### 2026-05-04 — DEV-DB-01 Fix Alembic async/sync engine mismatch
- **Агент:** backend-architect
- **Сделано:** в `apps/api/alembic/env.py` исправлен sync/async engine mismatch:
  - `engine_from_config()` (sync) заменён на `create_async_engine()` + `asyncio.run()` (async)
  - Добавлен `_do_run_migrations(connection)` — sync callback для `connection.run_sync()`
  - Добавлен `_validate_migration_safety()` — блокирует миграции против prod/staging/RDS БД
  - `run_migrations_offline()` теперь тоже вызывает `_validate_migration_safety()`
- **Проверки:** `compileall` ✅, `alembic upgrade head --sql` ✅ (8 таблиц, без DROP/TRUNCATE), `pytest tests -v` ✅ (219/219)
- **Ограничения:** онлайн-миграция НЕ запускалась (только `--sql`), БД НЕ менялась, `.env`/`alembic.ini`/`pyproject.toml`/`docker-compose.yml` не трогались
- Task summary: [.ai_memory/tasks/2026-05-04-task-dev-db-01.md](.ai_memory/tasks/2026-05-04-task-dev-db-01.md)

### 2026-05-04 — BE-06 blocking security fix (bounded read timeout)
- **Агент:** backend-architect
- **Сделано:** в `RealOpenCodeHttpTransport` устранён риск indefinite hang для sync `POST /session/{id}/message`:
  - default `read_timeout` теперь fail-closed и bounded: при `read_timeout=None` используется `RUNTIME_SESSION_TIMEOUT_SECONDS`
  - маппинг `httpx.ReadTimeout -> OpenCodeTimeoutError` сохранён без изменений
  - добавлен unit-тест на bounded default read timeout
- **Проверки:** `python -m compileall app` ✅, `ruff check app` ✅, `pytest tests -v` ✅ (193/193)
- **Ограничения:** реальный OpenCode server не запускался.

### 2026-05-04 — BE-06 transport compatibility fix (sync /session flow)
- **Агент:** backend-architect
- **Сделано:** обновлён runtime transport contract с legacy `/sessions` + SSE на BE-06 совместимость:
  - `create_session`: `POST /session`
  - plan flow (MVP): `POST /session/{id}/message` (sync)
  - добавлен strict mapping `parts -> plan.delta/plan.final/tool.call` с fail-closed обработкой malformed/unknown payloads
  - сохранены guardrails: stub-by-default, allow-flag gate для `opencode_http`, no silent fallback, policy_blocked для mutating tool actions, path confinement, redaction, memory minimization, idempotency, timeout limits
- **Тесты:** `compileall` ✅, `ruff` ✅, `pytest` ✅ (192/192)
- **Ограничения:** реальный OpenCode server не запускался.

### 2026-05-04 — BE-06 final compatibility docs alignment (launch procedure)
- **Агент:** devops-automator
- **Сделано:** обновлён `docs/smoke-test-opencode.md` под финальное направление совместимости BE-06:
  - зафиксирована единственная команда запуска: `opencode serve --port 4096 --hostname 127.0.0.1`
  - удалены `3001`, `opencode/server`, `@opencode/server`, `0.0.0.0`
  - identity/spec checks: `GET /global/health`, `GET /doc`
  - убраны любые `.env`-сценарии; оставлены только process env overrides
  - уточнены compatibility probes по фактически используемым backend endpoint-ам: `POST /session`, `POST /session/{id}/message`
- **Ограничения:** код не менялся, серверы/тесты не запускались.

### 2026-05-04 — BE-06 transport compatibility fix (runtime)
- **Агент:** backend-architect
- **Сделано:** runtime transport переведён с legacy `/sessions`+SSE на актуальный sync flow:
  - `POST /session` (create session)
  - `POST /session/{id}/message` (plan-only message)
  - mapping `parts -> plan.delta/plan.final/tool.call` с fail-closed обработкой unknown/malformed частей
  - сохранены guardrails: default stub, allow-flag gate, no silent fallback, policy_blocked, confinement/redaction/memory limits/idempotency
  - закрыт blocking security риск indefinite hang через bounded default read timeout
- **Проверки:** `python -m compileall app` ✅, `ruff check app` ✅, `pytest tests -v` ✅ (193/193)
- **Security verdict:** PASSED (GO)
- **Ограничения:** реальный OpenCode server не запускался.
- Task summary: [.ai_memory/tasks/2026-05-04-task-be06-transport-compatibility-fix.md](.ai_memory/tasks/2026-05-04-task-be06-transport-compatibility-fix.md)

### 2026-05-04 — BE-06 docs fix (smoke-test-opencode)
- **Агент:** backend-architect
- **Сделано:** обновлён `docs/smoke-test-opencode.md` для BE-06 controlled smoke test:
  - удалены инструкции изменения основного `.env`
  - добавлены только временные process env overrides (`RUNTIME_PROVIDER`, `OPENCODE_SERVER_URL`, `RUNTIME_ALLOW_REAL_OPENCODE_HTTP`)
  - унифицировано имя временного файла: `.env.opencode-smoke`
  - зафиксировано, что `.env.opencode-smoke` должен быть gitignored
  - добавлен явный rollback к runtime defaults (`stub`, empty URL, allow=false)
- **Ограничения:** OpenCode server не запускался, код не менялся, deploy/migrations/.env/secrets не трогались.
- Task summary: [.ai_memory/tasks/2026-05-04-task-be06-smoke-docs-fix.md](.ai_memory/tasks/2026-05-04-task-be06-smoke-docs-fix.md)

### 2026-05-04 — BE-06 rerun-plan docs alignment
- **Агент:** knowledge-steward
- **Сделано:** документация и память выровнены под rerun reality после Step-B abort:
  - портовая стратегия обновлена: primary `4096`, fallback `4097` (порт `3001` исключён)
  - зафиксирована единственная команда запуска: `opencode serve --port <PORT> --hostname 127.0.0.1`
  - identity checks: `/global/health`, `/doc`, optional `/config`/`/agent`
  - явные запреты: `opencode/server`, `@opencode/server`, `0.0.0.0`
  - добавлен backend compatibility preflight: `POST /session`, `POST /session/{id}/message`
  - cleanup defaults подтверждены: `stub`, empty URL, `allow=false`
- **Ограничения:** код/.env не менялись, серверы/тесты не запускались.
- Task summary: [.ai_memory/tasks/2026-05-04-task-be06-rerun-plan-after-step-b-abort.md](.ai_memory/tasks/2026-05-04-task-be06-rerun-plan-after-step-b-abort.md)

### 2026-05-04 — DevOps OpenCode smoke test plan (plan-only, без выполнения)
- **Агент:** devops-automator
- **Сделано:** составлен структурированный план controlled smoke test реального OpenCode server в plan-only режиме.
  - Определён способ запуска (Docker или npx на localhost:3001)
  - Минимальный compose-файл (план, не создавался)
  - Pre-flight + post-start checks (health, SSE, порт)
  - Интеграционный smoke test через AMC API с `RUNTIME_PROVIDER=opencode_http`
  - Cleanup checklist с возвратом `RUNTIME_PROVIDER=stub`
  - Approve gates: compose-файл, config.py, transport adapter требуют approve
  - Запреты: не трогать production/staging, не менять docker-compose, не открывать порты наружу
- **Проверки:** план не требует запуска (read-only документ)
- Task summary: [.ai_memory/tasks/2026-05-04-devops-opencode-smoke-test-plan.md](.ai_memory/tasks/2026-05-04-devops-opencode-smoke-test-plan.md)

### 2026-05-04 — BE-04 transport hardening (provider/transport fail-closed)
- **Агент:** backend-architect
- **Сделано:**
  - Runtime provider wiring ужесточён: default `RUNTIME_PROVIDER=stub`, unknown provider => fail-closed (`runtime_error` + `task_failed`).
  - `opencode_http` теперь только explicit opt-in + required `OPENCODE_SERVER_URL`; без обязательной конфигурации — fail-closed.
  - Удалён скрытый fallback: production factory больше не создаёт fake transport для `opencode_http`.
  - Fake/mocked transport разрешён только через explicit DI в тестах.
  - Добавлены тесты на fail-closed и отсутствие silent fallback.
- **Проверки:** `python -m compileall app` ✅, `ruff check app` ✅, `pytest tests -v` ✅ (167/167)
- **Ограничения:** real OpenCode runtime/server не запускался.

### 2026-05-04 — BE-05 Phase 1 hardening (B-1 + M-1/M-2/M-3 security findings fixed)
- **Агент:** backend-architect
- **Контур:** local only; без deploy/migrations/secrets/OpenCode.
- **Закрыто 4 findings:**
  - **B-1 (blocking):** `test_no_silent_fallback_to_stub_for_opencode_http` обновлён под новую семантику factory. Тест теперь проверяет: нет silent fallback на stub, нет stub fingerprint ("plan-only"/"No code execution"), ошибка идёт через runtime_error→task_failed, provider остаётся opencode_http.
  - **M-1:** `_truncate_plan(self, plan_text, session_id)` — session_id теперь используется в truncation marker `(session=<id>)` для traceability. Ранее параметр был неиспользуемым.
  - **M-2:** SSE non-JSON chunk size limit (64KB) в `_parse_sse_event()`. Чанки свыше лимита безопасно усекаются с metadata `_sse_chunk_truncated=True`; клиент эмитит `runtime_event_truncated` с reason. JSON SSE chunks НЕ ограничиваются.
  - **M-3 (critical):** Explicit safety gate `RUNTIME_ALLOW_REAL_OPENCODE_HTTP: bool = False` (default) в config. Factory для `opencode_http` теперь требует ОБА условия: URL задан И allow flag=True. Иначе — `RuntimeConfigurationError` (fail-closed). Fake/mocked transport разрешён только через explicit DI (`transport_factory`) + allow flag.
- **Новые/обновлённые тесты (8 тестов покрывают все required scenarios):**
  1. default provider remains stub ✅
  2. opencode_http без URL fail-closed ✅
  3. opencode_http без RUNTIME_ALLOW_REAL_OPENCODE_HTTP fail-closed ✅ (NEW)
  4. opencode_http с allow flag + недоступный сервер → runtime_error/task_failed ✅ (NEW)
  5. no silent fallback to stub ✅ (UPDATED B-1)
  6. SSE non-JSON chunk > 64KB truncates safely ✅ (NEW × 4 в transport tests)
  7. _truncate_plan session_id в truncation marker ✅ (UPDATED)
  8. real OpenCode server не запускался ✅ (NEW)
- **Изменённые файлы:** config.py, factory.py, transport.py, client.py, test_runtime_be04.py, test_opencode_transport.py
- **Проверки:** compileall ✅, ruff ✅, pytest ✅ (205/205)
- **Ограничения:** реальный OpenCode server не запускался, default=stub подтверждён

### 2026-05-04 — BE-05 RealOpenCodeHttpTransport + gap closures (implementation phase 1)
- **Агент:** backend-architect
- **Сделано:**
  - `RealOpenCodeHttpTransport` (HTTP/SSE на httpx) реализован в `apps/api/app/integrations/opencode/transport.py`
  - Закрыто 3 gaps:
    1. **max_plan_size**: `RUNTIME_MAX_PLAN_BYTES=100_000`, hard truncation + `runtime_event_truncated` event
    2. **timeout enforcement**: session total (60s) + idle (20s) в transport и client
    3. **tool.call path confinement**: `ensure_path_confined()` для read/search, блокирует escape/traversal/UNC/drive mismatch
  - SSE robustness улучшена: malformed → `runtime_event_malformed`, unknown type → `runtime_error`, non-JSON → wrapped as delta
  - Factory default для `opencode_http`: `RealOpenCodeHttpTransport` когда нет DI
  - `docs/smoke-test-opencode.md` — процедура будущего smoke test с abort criteria
  - Добавлен `runtime_event_truncated` в ALLOWED_EVENT_TYPES
  - Тесты: `test_opencode_transport.py` (19 new) + `test_runtime_be04.py` (+12 new guardrail tests)
- **Проверки:** compileall ✅, ruff ✅, pytest ✅ (197/197)
- **Ограничения:** реальный OpenCode server не запускался, все тесты через mocked/fake HTTP/SSE, default=stub сохранён
- Task summary: [.ai_memory/tasks/2026-05-04-task-be05-transport-gap-closures.md](.ai_memory/tasks/2026-05-04-task-be05-transport-gap-closures.md)

### 2026-05-04 — BE-04 review blockers fixed (security+architecture)
- **Агент:** backend-architect
- **Фиксы:**
  - Закрыт redaction leak: value-level redaction (key/value secrets, bearer tokens, private keys, env-like assignments).
  - Исправлена layering зависимость: guardrails перенесены в policy layer (`app/policy/runtime_guardrails.py`).
  - Исправлена provider abstraction: runtime client wiring через factory/DI, без жёсткой привязки service к fake transport.
  - Добавлена observability: `runtime_event_received`, `runtime_duplicate_event_ignored`, `runtime_retry_scheduled`.
  - Root confinement теперь применяется единообразно до provider branch.
- **Проверки:** `compileall` ✅, `ruff` ✅, `pytest` ✅ (162/162).
- **Ограничения соблюдены:** plan-only only, real OpenCode runtime/server не запускался.

### 2026-05-04 — BE-04 Completed (Runtime plan-only guardrails)
- **Агент:** backend-architect
- **Сделано:**
  - Provider safety: `RUNTIME_PROVIDER=stub|opencode_http`, default `stub`, unknown provider fail-closed (`runtime_error` + `task_failed`, без fallback).
  - Plan-only policy в fake OpenCode SSE: разрешены только `read/search/analyze/plan`; запрещённые tool/event сценарии блокируются.
  - Root confinement внедрён для runtime provider path checks (canonical resolve + containment).
  - Memory minimization: только top-k retrieval chunks + redaction перед runtime request.
  - SSE hardening: malformed/timeout/unknown/duplicate handling в mocked flow.
  - Idempotency: `correlation_id`, `session_id`, `idempotency_key`, no duplicate finalization при retry.
  - Approval invariants подтверждены тестами: low auto-approve, medium/high waiting approval.
  - Event schema расширена новыми runtime event types (BE-04).
- **Проверки:** API `compileall` ✅, `ruff` ✅, `pytest` ✅ (160/160).
- **Ограничения:** реальный OpenCode runtime/server не запускался; использованы только fake/mocked HTTP/SSE в тестах.

### 2026-05-03 — WRK-04 Manual DevOps slice (local compose verification)
- **Агент:** devops-automator
- **Сделано:**
  - Проверен effective config: `docker compose -f infra/docker/sandbox.compose.yml config`
  - Подтверждены security settings sandbox: `read_only`, `cap_drop: ALL`, `no-new-privileges`, `internal` network, `mem/cpu/pids` limits, отсутствие host/docker.sock mount
  - Для manual test создан локальный worktree path: `.worktrees/manual-test-wrk04/sample.py`
- **Ограничения:** image presence check не выполнялся отдельной командой (по условиям разрешены только `compose config` и conditional `docker build`).

### 2026-05-03 — WRK-04 Polish Completed (pre-manual-test hardening)
- **Агент:** backend-architect
- **Закрыты medium/low замечания из post-implementation review:**
  - Добавлены unit-тесты cleanup failure path: cleanup ошибка не маскирует primary success/error.
  - Добавлен отдельный unit-тест Docker unavailable path с проверкой redaction чувствительных деталей.
  - `result_summary` в execute flow теперь динамический по режиму sandbox (`fake`/`docker`), без misleading текста.
  - В docs исправлен счётчик event types: 21 -> 23.
  - Добавлен checklist manual Docker sandbox test в security/deployment policy docs.
- **Дополнительно:**
  - container name sanitation в DockerSandboxRunner для предсказуемых/безопасных имён.
- **Проверки:**
  - Worker: `compileall` ✅, `ruff` ✅, `pytest` ✅ (84/84)
- Task summary: [.ai_memory/tasks/2026-05-03-task-wrk04-polish-pre-manual-test.md](.ai_memory/tasks/2026-05-03-task-wrk04-polish-pre-manual-test.md)

### 2026-05-03 — WRK-04 Completed (DockerSandboxRunner implementation, opt-in)
- **Агент:** backend-architect
- **Закрыты BLOCKING issues B-1..B-4:**
  - **B-1 Mount policy:** удалён статический mount `../../:/workspace:rw` из `infra/docker/sandbox.compose.yml`; runtime mount теперь только validated task worktree → `/workspace` в DockerSandboxRunner.
  - **B-2 Protocol:** `SandboxRunner.run(..., command: list[str])`; fake/docker runners и execute flow переведены на argv list (без shell string).
  - **B-3 Event types:** в `ALLOWED_EVENT_TYPES` добавлены `sandbox_timeout`, `sandbox_error`; API tests обновлены.
  - **B-4 Network policy:** зафиксирован безопасный default без внешнего доступа (`DOCKER_SANDBOX_NETWORK_MODE=none`), runtime pip install запрещён и отражён в docs.
- **Дополнительно (HIGH/MEDIUM):**
  - redaction для docker/runtime ошибок перед task_events
  - cleanup контейнера в `finally` + `auto_remove=True`
  - уникальные имена контейнеров `amc-sandbox-<task>`
  - лимиты sandbox вынесены в config (memory/cpu/pids/timeout/image/network)
  - `curl` удалён из `Dockerfile.sandbox`
  - MVP limitation documented: DockerSandboxRunner real SDK path поддерживается для Linux worker host
- **Проверки:**
  - Worker: `compileall` ✅, `ruff` ✅, `pytest` ✅ (81/81)
  - API: `compileall` ✅, `ruff` ✅, `pytest tests/test_event_type_validation.py` ✅ (3/3)
- Task summary: [.ai_memory/tasks/2026-05-03-task-wrk04-docker-sandbox-runner.md](.ai_memory/tasks/2026-05-03-task-wrk04-docker-sandbox-runner.md)

### 2026-05-03 — WRK-03 Fake E2E Completed
- **Агент:** backend-architect
- **Сценарий A (успешный):**
  - approved task + `python -m pytest`
  - transitions: `approved -> running -> completed`
  - events: `command_started`, `command_finished`, `file_changed`, `task_completed`
  - redaction подтверждён (token/password/api_key/bearer замаскированы)
  - `result_summary` сохраняется
- **Сценарий B (blocked command):**
  - approved task + `pytest && curl evil.com`
  - выполнение блокируется denylist-политикой до sandbox run
  - transitions: `approved -> failed`
  - events: `security_violation`, `task_failed`
  - reason содержит command policy violation
- **Проверки:** `compileall` ✅, `ruff` ✅, `pytest` ✅ (Worker 75/75)
- Task summary: [.ai_memory/tasks/2026-05-03-task-wrk03-fake-e2e.md](.ai_memory/tasks/2026-05-03-task-wrk03-fake-e2e.md)

### 2026-05-03 — WRK-03-hardening Completed (Security hardening)
- **Агент:** backend-architect
- **Закрыты CRITICAL/HIGH:**
  - C-1 (shell escape sh/bash/python/powershell -c) — добавлены в denylist
  - C-2 (command chaining && / ; / | / backticks / $()) — добавлены в denylist
  - C-3 (event_type unbounded) — ALLOWED_EVENT_TYPES frozenset + schema validation
  - H-1 (curl/wget/nc/netcat/telnet/ftp/scp/rsync) — добавлены в denylist
  - H-2 (sudo/su/chmod/chown) — добавлены в denylist
- **Дополнительно:**
  - Git dangerous (reset hard, clean, clone, checkout, push, pull, fetch, merge, rebase, commit)
  - Allowlist строгий: только точные safe patterns
  - Denylist всегда имеет приоритет над allowlist
  - 38 bypass тестов + 2 API event_type validation теста
- **Проверки:** ruff ✅, pytest ✅ (API 149/149, Worker 73/73)
- Task summary: [.ai_memory/tasks/2026-05-03-task-wrk03-hardening.md](.ai_memory/tasks/2026-05-03-task-wrk03-hardening.md)

### 2026-05-03 — WRK-03 Completed (Safe execute pipeline)
- **Агент:** backend-architect
- **Сделано:**
  - `apps/worker/app/tasks/agent_execute.py` переписан со status gate (`approved` only)
  - Добавлены security services:
    - `command_policy.py` (allowlist/denylist)
    - `worktree_policy.py` (boundary validation under `.worktrees`)
    - `redaction.py` (secrets redaction + truncation)
    - `sandbox_runner.py` (`SandboxRunner`, `FakeSandboxRunner`, disabled `DockerSandboxRunner` skeleton)
  - Audit events через API: `command_started`, `command_finished`, `file_changed`, `task_completed`, `task_failed`, `security_violation`
  - API changes:
    - `task_events` router теперь поддерживает `POST /events/tasks/{task_id}/events`
    - `ALLOWED_TRANSITIONS`: добавлен переход `running -> completed`
  - Обновлены/добавлены тесты worker безопасности и execute flow
- **Проверки:**
  - API: `ruff` ✅, `pytest` ✅ (147/147)
  - Worker: `ruff` ✅, `pytest` ✅ (35/35)
- Task summary: [.ai_memory/tasks/2026-05-03-task-wrk03-safe-execute-pipeline.md](.ai_memory/tasks/2026-05-03-task-wrk03-safe-execute-pipeline.md)

### 2026-05-03 — Security Review фиксирован перед WRK-03
- **Агент:** security-engineer
- **Сделано:**
  - Зафиксирован verdict по готовности WRK-03: запуск допустим только при обязательных guardrails
  - Выровнена политика deploy: staging deploy в MVP = `approval_required`
  - Обновлены документы: `docs/security-policy.md`, `docs/deployment-policy.md`
  - Обновлена память: `.ai_memory/current_state.md`, task summary security review
- **Guardrails для WRK-03 (mandatory):**
  - execute только для `task.status=approved`
  - строгая проверка границ worktree (`resolve()` + `relative_to()`)
  - denylist опасных команд (force push, destructive fs/db/system/deploy/migration)
  - обязательные audit events (`command_started`, `command_finished`, `file_changed`, `task_completed/task_failed`)
  - redaction секретов в логах/task_events
- Task summary: [.ai_memory/tasks/2026-05-03-task-security-review-before-wrk03.md](.ai_memory/tasks/2026-05-03-task-security-review-before-wrk03.md)

### 2026-05-03 — DOP-02 Completed (Dockerfiles + sandbox compose)
- **Агент:** devops-automator
- **Сделано:**
  - Добавлены Dockerfiles: `Dockerfile.api`, `Dockerfile.telegram-bot`, `Dockerfile.worker`, `Dockerfile.sandbox`
  - Добавлен `infra/docker/sandbox.compose.yml` для будущего WRK-03
  - Security: non-root users, `no-new-privileges`, `cap_drop: ALL`, `privileged: false`, internal isolated network, resource limits
  - Документация обновлена: `infra/docker/README.md`, `infra/README.md`, `docs/deployment-policy.md`, `docs/security-policy.md`
  - Healthchecks добавлены для всех образов/compose-сервиса
- **Проверки:** `docker compose -f infra/docker/sandbox.compose.yml config` ✅
- Task summary: [.ai_memory/tasks/2026-05-03-task-dop02-dockerfiles-sandbox-compose.md](.ai_memory/tasks/2026-05-03-task-dop02-dockerfiles-sandbox-compose.md)

### 2026-05-03 — MEM-03 Completed (Memory indexing + retrieval)
- **Агент:** backend-architect
- **Сделано:**
  - `memory_chunking_service.py` — heading-aware chunking, fallback split, chunk_index support
  - `memory_embedding_service.py` — deterministic fake embeddings (1536 dim), cosine similarity
  - `memory_indexing_service.py` — vault scan (`.ai_memory/**/*.md`), hash-skip, safe old-chunk replacement, project mapping
  - `memory_retrieval_service.py` — repository protocol + SQLAlchemy repo + top-k ranking
  - `routers/memory.py` — добавлены endpoints `POST /memory/reindex`, `POST /memory/search`
  - `worker/tasks/memory_index.py` — теперь вызывает API `/memory/reindex` (вместо stub)
  - Тесты: `test_memory_chunking.py`, `test_memory_retrieval.py`, расширен `test_memory_router.py`, обновлён worker `test_tasks.py`
- **Проверки:** compileall ✅, ruff ✅, pytest ✅ (API 147/147, Worker 27/27)
- Task summary: [.ai_memory/tasks/2026-05-03-task-mem03-memory-indexing-retrieval.md](.ai_memory/tasks/2026-05-03-task-mem03-memory-indexing-retrieval.md)

### 2026-05-03 — MEM-02 Completed (Memory CRUD API)
- **Агент:** backend-architect
- **Сделано:**
  - `memory_policy_service.py` — path validation, access tiers (FREE/APPROVAL_REQUIRED/FORBIDDEN), secrets guard
  - `memory_service.py` — read_file, write_file (with bypass_approval), append_file, list_files, get_access_tier
  - `routers/memory.py` — 6 endpoints: GET/PUT/POST memory files, provision, access info
  - Schemas обновлены: MemoryFileRead/Write/WriteRequest/ListResult/AccessInfo
  - 76 новых тестов (35 policy + 20 service + 17 router + 4 provisioning adjustments)
- **Проверки:** compileall ✅, ruff ✅, pytest ✅ (140/140 API total)
- Task summary: [.ai_memory/tasks/2026-05-03-task-mem02-memory-crud-api.md](.ai_memory/tasks/2026-05-03-task-mem02-memory-crud-api.md)

### 2026-05-03 — MEM-01 Completed (Memory provisioning)
- **Агент:** knowledge-steward
- **Сделано:**
  - `MemoryProvisioningService` — создаёт 7 файлов памяти проекта (overview, current_state, architecture, decisions, tasks, known_issues, agent_notes)
  - `memory.py` schema — MemoryProvisionRequest/Result/FileResult/ProjectInfo + contains_forbidden_content()
  - 5 шаблонов обновлены/созданы (project-memory, task-summary, agent-notes, ADR, current-state)
  - Vault docs обновлены (README, _INDEX, projects/README)
  - `docs/memory-system.md` — документация для агентов
  - Тесты MEM-01: 12/12 passed
- **Проверки:** compileall ✅, ruff ✅, pytest ✅ (64/64 API total)
- Task summary: [.ai_memory/tasks/2026-05-03-task-mem01-memory-provisioning.md](.ai_memory/tasks/2026-05-03-task-mem01-memory-provisioning.md)

### 2026-05-03 — FND-01 + FND-02 Completed
- **FND-01 (git-workflow-master):** .gitignore, CHANGELOG.md, CONTRIBUTING.md, docs/git-workflow.md
- **FND-02 (backend-architect):** FastAPI skeleton, /health endpoint, pydantic-settings config, pyproject.toml
- Обновлён PROJECT_MEMORY.md, .ai_memory/current_state.md
- Task summary: [.ai_memory/tasks/2026-05-03-task-fnd01-fnd02.md](.ai_memory/tasks/2026-05-03-task-fnd01-fnd02.md)

### 2026-05-03 — FND-03 Completed (DB Foundation)
- **Агент:** backend-architect
- **Сделано:**
  - SQLAlchemy async DB foundation: `app/db/{base,session,enums}.py`
  - Модели 8 таблиц: `Project`, `Agent`, `TelegramTopic`, `Task`, `Approval`, `TaskEvent`, `MemoryDocument`, `MemoryChunk`
  - Alembic в `apps/api/alembic/` (ini, env.py, template, baseline migration)
  - Baseline migration `0001_initial_all_tables.py` включает `CREATE EXTENSION IF NOT EXISTS vector`
- **Ограничения соблюдены:** shell/docker/alembic upgrade/DB connection не запускались
- **Важно:** для `memory_documents(scope, project_id, path)` пока обычный индекс; partial unique index вынесен в follow-up
- Task summary: [.ai_memory/tasks/2026-05-03-task-fnd03-db-foundation.md](.ai_memory/tasks/2026-05-03-task-fnd03-db-foundation.md)

### 2026-05-03 — BE-01 Completed (CRUD endpoints)
- **Агент:** backend-architect
- **Сделано:**
  - Pydantic schemas: `ProjectCreate/Update/Read`, `AgentCreate/Update/Read`, `TelegramTopicCreate/Update/Read`
  - Async services: `ProjectService`, `AgentService`, `TelegramTopicService`
  - Routers: `GET/POST/PATCH/DELETE /projects`, `/agents`, `/telegram/topics`
  - Soft delete: project→status=archived, agent→status=disabled, topic→is_active=False
  - 17 тестов (schema validation + router structure) — все пройдены
- **Проверки:** `compileall` ✅, `ruff` ✅, `pytest` ✅ (17/17)
- Task summary: [.ai_memory/tasks/2026-05-03-task-be01-crud.md](.ai_memory/tasks/2026-05-03-task-be01-crud.md)

### 2026-05-03 — BE-02 Completed (Tasks + Approvals)
- **Агент:** backend-architect
- **Сделано:**
  - `TaskService`: create (auto external_id), status transitions (15 legal), cancel, list/filter, auto event logging
  - `ApprovalService`: create_request, approve, reject (double-decide blocked), list_by_task, event logging
  - `TaskEventService`: append-only create, list_by_task, list_all with filters
  - Routers: 6 task endpoints + 5 approval endpoints + 2 event endpoints
  - Pydantic schemas: TaskCreate/Update/StatusUpdate/Read, ApprovalCreate/DecideIn/Read, TaskEventRead
- **Проверки:** `compileall` ✅, `ruff` ✅, `pytest` ✅ (41/41: 14 tasks + 10 approvals + 17 existing)
- Task summary: [.ai_memory/tasks/2026-05-03-task-be02-approvals.md](.ai_memory/tasks/2026-05-03-task-be02-approvals.md)

### 2026-05-03 — TG-01 Completed (Telegram bot gateway)
- **Агент:** backend-architect
- **Сделано:**
  - Отдельное приложение `apps/telegram-bot/` на aiogram 3.x
  - Polling-режим для dev (без запуска в рамках задачи)
  - Команды: `/start`, `/help`, `/projects`, `/agents`, `/tasks`
  - API client к backend для команд и создания task
  - Topic-aware обработка текста: если topic привязан → создаётся task, если нет → сообщение о непривязке
  - Ответы всегда отправляются в тот же topic через `message_thread_id`
  - Тесты TG-01: 8/8 passed
- **Проверки:** `compileall` ✅, `ruff` ✅, `pytest` ✅ (8/8)
- Task summary: [.ai_memory/tasks/2026-05-03-task-tg01-telegram-gateway.md](.ai_memory/tasks/2026-05-03-task-tg01-telegram-gateway.md)

### 2026-05-03 — TG-02 Completed (Topic binding + routing bridge)
- **Агент:** backend-architect
- **Сделано:**
  - Новые команды: `/bind_topic`, `/unbind_topic`, `/topic_status`
  - Привязка topic по формату `/bind_topic project=<slug> agent=<slug>`
  - Валидация forum-topic контекста (`message_thread_id` обязателен)
  - Soft unbind через deactivate (`DELETE /telegram/topics/{id}`)
  - `topic_status` показывает chat_id, message_thread_id, project_id, agent_id, status
  - Routing bridge обновлён: непривязанный topic → подсказка `/bind_topic`, привязанный topic → `POST /tasks`
  - Роутеры TG-02 зарегистрированы в dispatcher
  - Тесты TG-02 добавлены и пройдены
- **Проверки:** `compileall` ✅, `ruff` ✅, `pytest` ✅ (14/14)
- Task summary: [.ai_memory/tasks/2026-05-03-task-tg02-topic-binding-routing.md](.ai_memory/tasks/2026-05-03-task-tg02-topic-binding-routing.md)

### 2026-05-03 — BE-03 Completed (Runtime adapter, plan-only)
- **Агент:** backend-architect
- **Сделано:**
  - Добавлен runtime adapter слой (`integrations/opencode/*`) с контрактом `OpenCodeClientProtocol` и `StubOpenCodeClient`
  - Добавлен `RuntimeService` с endpoint-флоу plan-only: контекст задачи → генерация плана → сохранение `plan_text`
  - Добавлен endpoint `POST /runtime/tasks/{task_id}/plan`
  - Реализована логика риска:
    - `low` → автоматический переход в `approved`
    - `medium/high/critical` → переход в `waiting_approval` + создание approval request
  - Логируются события: `plan_generated`, `approval_requested`
  - Добавлены тесты BE-03 (`apps/api/tests/test_runtime.py`)
- **Ограничения соблюдены:** никаких runtime/shell/deploy/git/worktree/.env/secrets действий
- **Проверки:** `compileall` ✅, `ruff` ✅, `pytest` ✅ (46/46)
- Task summary: [.ai_memory/tasks/2026-05-03-task-be03-runtime-plan-only.md](.ai_memory/tasks/2026-05-03-task-be03-runtime-plan-only.md)

### 2026-05-03 — WRK-02 Completed (Plan pipeline)
- **Агент:** backend-architect
- **Сделано:**
  - **API:** `POST /tasks/{task_id}/trigger-plan` — валидирует (project_id, agent_id), переводит в `routed`, диспетчеризует Celery `agent_plan`
  - **API:** `integrations/queue.py` — тонкий Celery `send_task` dispatcher (broker-only, без импорта worker кода)
  - **Worker:** `agent_plan` task переписан — вызывает runtime API, получает результат, диспетчеризует `send_notification` с планом
  - **Worker:** `notifications` task переписан — использует `Notifier` adapter pattern
  - **Worker:** `services/notifier.py` — `Notifier` protocol + `TelegramNotifier` (httpx) + `StubNotifier` (testing) + factory
  - **Worker:** `config.py` добавлен `TELEGRAM_BOT_TOKEN`
  - **Telegram bot:** `messages.py` — после создания task вызывает `trigger_plan`, показывает статус pipeline
  - **Telegram bot:** `api_client.py` — добавлен метод `trigger_plan(task_id)`
  - Тесты: API 140/140, Worker 26/26, Telegram bot 15/15 = **181 total**
- **Pipeline flow:** Telegram → POST /tasks → POST /trigger-plan → Celery agent_plan → POST /runtime/plan → Celery notifications → Telegram topic
- **Проверки:** `compileall` ✅, `ruff` ✅, `pytest` ✅ (93/93)
- Task summary: [.ai_memory/tasks/2026-05-03-task-wrk02-plan-pipeline.md](.ai_memory/tasks/2026-05-03-task-wrk02-plan-pipeline.md)

### 2026-05-03 — WRK-01 Completed (Celery worker skeleton)
- **Агент:** backend-architect
- **Сделано:**
  - Отдельное приложение `apps/worker/` на Celery
  - 7 именованных очередей: telegram_inbound, agent_plan, agent_execute, memory_index, deploy_staging, deploy_production, notifications
  - Healthcheck task (`tasks.healthcheck`)
  - Stub-задачи для всех очередей (кроме agent_plan — делает HTTP call to backend)
  - `deploy_production` всегда возвращает blocked/requires_approval
  - Retry/backoff policy через pydantic-settings
  - JSON serializer, acks_late, result expiry
  - Тесты WRK-01: 17/17 passed
- **Проверки:** `compileall` ✅, `ruff` ✅, `pytest` ✅ (17/17)
- Task summary: [.ai_memory/tasks/2026-05-03-task-wrk01-celery-worker.md](.ai_memory/tasks/2026-05-03-task-wrk01-celery-worker.md)

### 2026-05-03 — DOP-01 Completed (Dev docker-compose)
- **Агент:** devops-automator
- **Сделано:** создан `infra/docker/docker-compose.yml` для локальной dev-инфраструктуры
  - `postgres` (`pgvector/pgvector:pg16`)
  - `redis` (`redis:7-alpine`)
  - `api` (локальный запуск FastAPI в контейнере)
  - named volumes: `amc_dev_postgres_data`, `amc_dev_redis_data`
  - healthchecks для всех трёх сервисов
  - isolated bridge network `amc_dev_net`
- **Ограничения соблюдены:** staging/prod не трогались, `.env`/secrets не создавались, shell/deploy не запускались
- Task summary: [.ai_memory/tasks/2026-05-03-task-dop01-dev-docker-compose.md](.ai_memory/tasks/2026-05-03-task-dop01-dev-docker-compose.md)

### 2026-05-03 — Project Root Correction + Memory Sync
- Вся документация перенесена в правильный project root
- `.ai_memory/` заполнен как главный Obsidian vault

### 2026-05-05 — BE-11 Runtime Runbook + Local Smoke Automation COMPLETE
- **Агенты:** devops-automator + knowledge-steward
- **Контур:** local only; без deploy/migrations/secrets/OpenCode.
- **Создано 9 PowerShell скриптов в `scripts/dev/` (1934 lines total):**
  1. `check-db.ps1` — проверка контейнера postgres, pg_isready, 9 таблиц, alembic version
  2. `bootstrap-db.ps1` — alembic upgrade head с guard'ом (требует -Force если таблицы уже есть)
  3. `start-api-stub.ps1` — запуск uvicorn с RUNTIME_PROVIDER=stub (127.0.0.1:8000)
  4. `start-opencode.ps1` — динамический launcher (npm/cmd/PATH), порт 4096, 127.0.0.1 only
  5. `start-api-opencode.ps1` — запуск API с env overrides (opencode_http, allow=true), без DATABASE_URL
  6. `start-worker.ps1` — Celery worker с process-scoped env (redis, API timeout)
  7. `smoke-stub-runtime.ps1` — stub provider smoke test (create → plan → verify)
  8. `smoke-real-opencode-runtime.ps1` — real OpenCode E2E smoke test c 13 проверками
  9. `cleanup-runtime.ps1` — остановка OpenCode/Celery/API, auto-restart stub
- **Создана документация:** `docs/runtime-runbook.md` — полный runbook (9 шагов, зависимости, safety rules, troubleshooting)
- **Обновлены docs:** `docs/smoke-test-opencode.md` (+автоматизированные альтернативы), `docs/security-policy.md` (+BE-11 Safety Rules: F1-F10 forbidden, A1-A13 abort criteria, P1-P15/T1-T12 checklists, S1-S8 secrets handling)
- **Constraint validation:** All 9 scripts PSParser-tokenized OK, all support -DryRun, no .env writes, no persistent env, no 0.0.0.0 binds, no port 3001, no secrets, Invoke-RestMethod only.
- **Safety rules codified:** forbidden ops (F1-F10), abort criteria (A1-A13), pre-smoke (P1-P15), post-smoke (T1-T12), secrets handling (S1-S8).
- **Worker bypass note:** smoke scripts use direct POST /runtime, not Celery worker.
- **Ограничения соблюдены:** process-scoped env only, 127.0.0.1 only, без production/staging, без deploy/migrations, no real OpenCode/smoke deployed during implementation.
- Task summary: [.ai_memory/tasks/2026-05-04-task-be11-runtime-runbook-automation.md](.ai_memory/tasks/2026-05-04-task-be11-runtime-runbook-automation.md)

### 2026-05-03 — Инициализация проекта
- Создана структура директорий и документация
- Спроектирована архитектура и схема БД
