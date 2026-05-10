# VPS-08B — Telegram Mini App + Forum Topics Architecture Audit

Date: 2026-05-10  
Agent: studio-orchestrator  
Target: VPS `45.130.213.12` + local repo `F:\dev\agentrouter`  
Status: **completed (read-only audit)**

## Scope / safety
- Read-only audit only.
- No Telegram messages sent.
- No topics/groups created or edited.
- No OpenCode start.
- No real agent tasks run.
- No DB mutations.
- No service restarts.
- No migrations.
- No secrets printed.

## Baseline
- Local sync: `main...origin/main`, clean tree, latest includes VPS-08A + VPS-07D commits.
- Runtime baseline (server): PASS
  - SSH (`agentmc`, `root`) OK
  - 5/5 containers healthy
  - HTTPS `/health` OK
  - 4 timers active
  - UFW unchanged (22/80/443)

## Local/server repo sync status
- Local repo is current with origin.
- Deployed server repo is clean but on older commit chain than local/origin main.
- No pull performed (recorded as deployment drift blocker).

## Frontend / Mini App discovery
1. Existing frontend app?
   - **No implemented app**. Only `apps/web/README.md` planning placeholder.
2. Stack detected?
   - Planned stack documented as React + Vite + TypeScript + Tailwind, but code absent.
3. Telegram WebApp SDK usage?
   - Not found (`Telegram.WebApp`, `window.Telegram`, `initData`, `WebAppInfo` absent).
4. Mini App auth/initData validation?
   - Not found.
5. Routing/navigation?
   - Not implemented (no frontend codebase).
6. Frontend deploy path?
   - Not implemented in runtime compose for production.
7. Served by API/Caddy or separate service?
   - No frontend service configured in current prod compose.
8. Custom UI needed from scratch?
   - **Yes** (foundation missing).

## Backend API inventory (Mini App relevant)

### Agents
- `POST /agents` create
- `GET /agents` list
- `GET /agents/{agent_id}` detail
- `PATCH /agents/{agent_id}` update
- `DELETE /agents/{agent_id}` soft-disable

### Tasks
- `POST /tasks` create
- `GET /tasks` list
- `GET /tasks/{task_id}` detail
- `PATCH /tasks/{task_id}` update
- `PATCH /tasks/{task_id}/status` status update
- `POST /tasks/{task_id}/cancel`
- `POST /tasks/{task_id}/trigger-plan`
- `GET /tasks/{task_id}/plan`
- `POST /tasks/{task_id}/callback-answer`

### Activity / events
- `GET /events` global list (system activity feed candidate)
- `GET /events/tasks/{task_id}/events` task activity

### Approvals
- `POST /approvals/tasks/{task_id}/approvals`
- `GET /approvals/tasks/{task_id}/approvals`
- `GET /approvals/{approval_id}`
- `POST /approvals/{approval_id}/approve`
- `POST /approvals/{approval_id}/reject`

### Telegram topics
- `POST /telegram/topics`
- `GET /telegram/topics`
- `GET /telegram/topics/{topic_id}`
- `PATCH /telegram/topics/{topic_id}`
- `DELETE /telegram/topics/{topic_id}`

### Missing for target Mini App UX
- No dedicated Mini App auth/initData verification endpoint.
- No explicit user/profile endpoint for per-user UI state.
- No dedicated aggregate dashboard endpoint (requires client composition from multiple endpoints).

## Telegram bot / topics code findings
1. Framework: **aiogram 3.x**.
2. Mini App button: **not implemented** (no web_app buttons).
3. Group/supergroup handling: yes via generic message handlers.
4. Forum topic recognition: implicit through `message.message_thread_id`.
5. `message_thread_id` parsed: yes.
6. `message_thread_id` persisted: yes (`telegram_topics.message_thread_id`, `tasks.telegram_thread_id`).
7. Outgoing targeting by thread: available via notifier payload `thread_id` path.
8. Special General topic logic: not hardcoded as orchestrator-specific policy.
9. topic→agent mapping: exists via `/bind_topic` + `/telegram/topics` + `kind/agent_id/project_id`.
10. Approvals topic explicit mode: schema supports `kind`, but no strict orchestration policy enforcement for dedicated topic roles.
11. System Logs topic explicit mode: same as above.
12. Admin-only access: present for approval/reject flows.
13. Approval flow topic-aware: partially (chat/thread metadata captured and audited).
14. Telegram triggers plan/execute: plan trigger exists; execute path exists in worker but not used in this audit.

## DB schema audit (read-only)
- Tables present: `agents`, `tasks`, `task_events`, `approvals`, `telegram_topics`, `security_audit_events`, etc.
- Relevant columns confirmed:
  - `tasks.telegram_chat_id`, `tasks.telegram_thread_id`, `tasks.agent_id`, status/risk/intent/payload
  - `telegram_topics.chat_id`, `telegram_topics.message_thread_id`, `telegram_topics.kind`, `agent_id`, `project_id`, `is_active`
  - `security_audit_events.chat_id`, `thread_id`, `task_id`, `approval_id`
- Row counts (deployed DB): all key orchestration tables currently `0`.
- Alembic version: `0002_add_security_audit_events`.

## Logs audit summary
- No Mini App activity evidence.
- Bot logs show API calls to agents/topics endpoints and polling startup.
- No explicit live forum-topic routing traffic or `message_thread_id` values observed in sampled logs.
- Worker logs show task registrations/queues, including `telegram_inbound` and `agent_plan`.

## Target architecture gap matrix (summary)

### Mini App block
- Launch button: missing
- WebApp auth/initData validation: missing
- Mobile dashboard/pages/components/design system: missing
- Frontend deploy/service path: missing
- API client layer for UI: partially available via backend REST, but no frontend implementation

### Topics block
- Topic parsing/persistence/mapping: present
- Dedicated General/Approvals/System Logs orchestration semantics: partially missing (kind exists, enforcement/policies absent)
- Topic-linked lifecycle/audit metadata: partially present
- OpenCode execution linked to topic/agent: conceptually wired via task metadata, not activated
- Safe dry-run/no-op and rollback switches: partially present in runtime/sandbox settings

## VPS-08C recommendation

**Selected option:** **Option A — VPS-08C Mini App foundation implementation** (with immediate subtrack for topic-policy hardening).

Why:
- Major blocker is absent Mini App frontend and WebApp auth flow.
- Backend already has core CRUD primitives for agents/tasks/approvals/topics.
- Topic plumbing exists but needs explicit role semantics for General/Approvals/Logs.

### Likely files to change in VPS-08C
- New frontend app under `apps/web/*` (React/Vite/TS/Tailwind).
- Bot handlers/keyboards to expose WebApp launch button.
- API: optional endpoint(s) for Mini App auth/initData verification + dashboard aggregation.
- Possible schema migration only if strict topic-role config tables/constraints are added.

### Migration needed?
- Not strictly for base UI.
- Possibly yes for robust topic-role policy model (if current `kind` field insufficient).

### Service/deploy impact later
- Yes, later stage will require deploy changes for serving frontend and bot WebApp URL wiring.

### Tests required
- Frontend unit/integration tests.
- API tests for WebApp auth endpoint (if added).
- Bot handler tests for WebApp button.
- Topic-policy tests (General/Approvals/Logs routing behavior).

### Safety risks
- WebApp auth integrity and replay protection.
- Permission boundaries for approve/reject in UI.
- Topic misrouting risks without strict policy constraints.

### Proposed gate for VPS-08C
- `CONFIRM_VPS08C_MINIAPP_FOUNDATION=yes`

## Safety closeout
- No Telegram messages sent: ✅
- No topics created/edited/deleted: ✅
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
  - `.ai_memory/tasks/2026-05-10-task-vps08b-miniapp-topics-audit.md`
- **Commit hash:** not committed (as requested)
