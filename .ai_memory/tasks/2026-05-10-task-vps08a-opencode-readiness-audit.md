# VPS-08A — Controlled OpenCode Readiness Audit

Date: 2026-05-10  
Agent: studio-orchestrator  
Target: VPS `45.130.213.12`  
Status: **completed (read-only audit)**

## Scope and safety
- Stage type: read-only audit only.
- OpenCode was **not started**.
- Real agent tasks were **not executed**.
- Production DB was **not modified**.
- Services were **not restarted**.
- Migrations were **not run**.
- Secrets were **not printed**.

## Baseline checks
- Local repo baseline: clean, `main...origin/main`, latest commit `d54b4e8 docs(vps): record restore drill validation`.
- Production runtime baseline: PASS
  - all 5 containers healthy
  - HTTPS `/health` OK
  - 4 timers active
  - UFW unchanged (22/80/443)

## OpenCode readiness discovery

### 1) Where OpenCode integration lives
- API integration layer:
  - `apps/api/app/integrations/opencode/factory.py`
  - `apps/api/app/integrations/opencode/transport.py`
  - `apps/api/app/integrations/opencode/client.py`
  - `apps/api/app/services/runtime_service.py`
- API trigger surface:
  - `POST /tasks/{task_id}/trigger-plan` in `apps/api/app/routers/tasks.py`
- Queue bridge:
  - `apps/api/app/integrations/queue.py` dispatches `tasks.agent_plan`
- Worker pipeline:
  - planning: `apps/worker/app/tasks/agent_plan.py`
  - execution: `apps/worker/app/tasks/agent_execute.py`
- Telegram command/admin surfaces:
  - `apps/telegram-bot/app/handlers/*`

### 2) Dry-run / sandbox support
- API runtime provider default is `stub` (`RUNTIME_PROVIDER=stub`).
- Real OpenCode path requires explicit gate:
  - `RUNTIME_PROVIDER=opencode_http`
  - `OPENCODE_SERVER_URL`
  - `RUNTIME_ALLOW_REAL_OPENCODE_HTTP=true`
- Worker execute sandbox default: `SANDBOX_RUNNER_MODE=fake`.
- Docker sandbox exists as opt-in (`docker` mode), with network `none` default in config.

### 3) What triggers execution paths
- Plan generation trigger: `POST /tasks/{id}/trigger-plan` (API) → Celery `tasks.agent_plan`.
- Runtime plan endpoint used by worker: `POST /runtime/tasks/{id}/plan`.
- Execution path exists separately (`tasks.agent_execute`), requires task status `approved` and command/worktree policies.

### 4) Existing safety checks
- Fail-closed runtime factory gating for real OpenCode transport.
- Policy checks for callback signatures/expiry and permission engine.
- Runtime path confinement and tool action restrictions.
- Runtime event/audit trail emission (`runtime_session_created`, `runtime_event_received`, `policy_blocked`, etc.).
- Redaction in runtime and worker logging paths.

### 5) Missing/blocked readiness item for production activation
- Server currently has no `opencode` binary in PATH (both `agentmc` and `root`).
- No running OpenCode process and no dedicated opencode systemd unit.

### 6) DB entities involved (read-only mapping)
- Core: `tasks`, `task_events`, `approvals`, `security_audit_events`.
- Runtime interactions are mediated through API status/event writes.

### 7) Telegram surfaces involved
- Bot handlers for task/status/plan/approval interactions (admin-gated paths).

### 8) Worker involvement
- Required for operational plan pipeline (`tasks.agent_plan`).
- Execution queue exists but was not used in this audit.

### 9) Env/service change needs for activation
- Activation of real OpenCode path would require explicit runtime env overrides.
- In production containers, runtime provider currently pinned to stub in compose template.
- Any real activation likely requires controlled config override and service restart window (not in VPS-08A).

## Process/service audit
- `pgrep -af 'opencode|open-code'`: no active OpenCode runtime process detected (only self-matching command line artifact).
- `systemctl list-units`: no opencode service unit found.
- `command -v opencode` (`agentmc`, `root`): not found.
- `opencode --version` (agentmc): no output (binary absent).

## Logs audit (redacted)
- API logs (tail/keyword scan): no active OpenCode execution traces.
- Worker logs: queue/task registration present (`tasks.agent_plan`, `tasks.agent_execute`, etc.), no live OpenCode run evidence.
- Telegram bot logs: normal polling/API calls; no OpenCode execution evidence.

## Local safe test discovery
- Candidate unit tests discovered:
  - `apps/api/tests/test_opencode_transport.py`
  - `apps/api/tests/test_tasks_plan_endpoint.py`
  - `apps/api/tests/test_security_*`
  - `apps/worker/tests/test_agent_plan_pipeline.py`
  - `apps/worker/tests/test_sandbox_runner.py`
  - `apps/worker/tests/test_execute_security.py`
- Tests were not executed in this stage to keep strict read-only runtime audit scope.

## VPS-08B recommended dry-run activation plan

Next recommended step (pre-activation): **Telegram Forum / Topics Orchestration Audit before OpenCode dry-run**.

### Objective
Run one **admin-only**, **single-task**, **plan-only** smoke flow to verify end-to-end runtime wiring without executing commands.

### Proposed steps
1. Pre-gate: `CONFIRM_VPS08B_OPENCODE_DRYRUN=yes`.
2. Validate OpenCode CLI/server availability in isolated/local-only mode.
3. Apply temporary runtime overrides only for test window (no persistent `.env` edits in repo).
4. Restart only required service(s) under explicit approved window (if needed for runtime provider switch).
5. Create one controlled low-risk test task (if absolutely required by flow) and trigger plan.
6. Verify only plan-related events (`runtime_session_created`, `runtime_event_received`, `plan_generated`), and no execute events.
7. Enforce timeout and abort criteria.
8. Restore defaults (`stub`, allow=false), verify runtime health, preserve audit trail.

### Answers to required VPS-08B planning questions
1. **What tested:** plan-only OpenCode request/response mapping and event trail.
2. **DB task row:** likely yes (single controlled task), non-destructive.
3. **OpenCode binary call:** yes, only server/runtime endpoint path.
4. **File modifications:** none in repo during run.
5. **Env changes:** temporary runtime overrides required.
6. **Service restart:** likely API and/or worker restart needed to apply runtime provider override.
7. **Dry-run/no-op guarantee:** keep execute pipeline disabled; verify no `command_started/command_finished/file_changed` events.
8. **Log checks:** keyword and event-type checks on api/worker/task_events only.
9. **Cleanup:** revert runtime to stub defaults; confirm health and no lingering OpenCode process.
10. **Rollback:** immediate revert to stub config + service health verification.
11. **Gate string:** `CONFIRM_VPS08B_OPENCODE_DRYRUN=yes`.

## Safety closeout
- OpenCode not started: ✅
- Real tasks not run: ✅
- Production DB not modified: ✅
- Services not restarted: ✅
- Migrations not run: ✅
- Secrets not printed: ✅

## Memory checkpoint
- **Memory updated:** yes
- **Files updated:**
  - `PROJECT_MEMORY.md`
  - `.ai_memory/current_state.md`
  - `.ai_memory/_INDEX.md`
  - `.ai_memory/tasks/2026-05-10-task-vps08a-opencode-readiness-audit.md`
- **Commit hash:** not committed (as requested)
