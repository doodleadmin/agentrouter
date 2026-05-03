# OpenCode Smoke Test Procedure

> **Status:** plan-only document. Real OpenCode server has NOT been run.
> **Purpose:** checklist for a future controlled smoke test of the `RealOpenCodeHttpTransport` + real OpenCode server integration.

---

## Pre-conditions

- [ ] `RUNTIME_PROVIDER=stub` confirmed (default)
- [ ] `OPENCODE_SERVER_URL` is empty or not set
- [ ] All existing tests pass: `pytest apps/api/tests -v`
- [ ] `compileall` passes: `python -m compileall app`
- [ ] `ruff check app` passes
- [ ] No production/staging servers involved
- [ ] No `.env` changes beyond the smoke test variables
- [ ] Docker sandbox mode is `fake` (not `docker`)

## Smoke Test Steps

### Step 1: Start OpenCode server

Start a real OpenCode server in **plan-only mode** on `localhost:3001`:

```bash
# Option A: Docker
docker run -d --name opencode-smoke \
  -p 127.0.0.1:3001:3001 \
  opencode/server:latest \
  --mode plan-only

# Option B: npx
npx @opencode/server --port 3001 --mode plan-only
```

**Verify:** `curl http://localhost:3001/health` returns 200.

### Step 2: Configure AMC for opencode_http

Set in `.env` (project root):

```env
RUNTIME_PROVIDER=opencode_http
OPENCODE_SERVER_URL=http://localhost:3001
RUNTIME_SESSION_TIMEOUT_SECONDS=30
RUNTIME_IDLE_TIMEOUT_SECONDS=10
```

Restart the API server.

### Step 3: Run integration smoke test

Create a test task through the existing API or Telegram bot, then trigger plan generation:

```bash
# Example: POST /tasks then POST /runtime/tasks/{id}/plan
# Expected: task transitions to 'approved' (low risk) or 'waiting_approval' (medium/high)
# Expected: plan_text is populated, no 'runtime_error' events
```

### Step 4: Verify events

```bash
curl http://localhost:8000/events/tasks/{task_id}/events | python -m json.tool
```

Expected events (subset):
- `runtime_session_created` — session was created on OpenCode server
- `runtime_event_received` — at least one SSE event received
- `plan_generated` — plan was successfully generated
- No `runtime_timeout`, `runtime_error`, or `policy_blocked`

### Step 5: Cleanup

```bash
# Stop OpenCode server
docker stop opencode-smoke && docker rm opencode-smoke

# Restore default config
# Remove or comment out RUNTIME_PROVIDER and OPENCODE_SERVER_URL from .env
# Restart API server
```

**Verify:** `RUNTIME_PROVIDER=stub` is active again.

## Abort Criteria

Stop the smoke test immediately if any of the following occurs:

1. **real code execution triggered** — any command actually runs (check task events for `command_started`, `command_finished`, `file_changed`)
2. **network escape** — OpenCode server attempts outbound connections beyond localhost
3. **file system writes** — any files modified outside `.worktrees/`
4. **secrets leaked** — any `.env`, token, or key appears in plan_text or task_events
5. **approval bypass** — medium/high/critical task transitions to `approved` without explicit approval
6. **provider fallback** — `runtime_error` occurs because OpenCode server is unreachable but task falls back to stub (Must NOT happen)

## Post-Smoke Checks

After cleanup, run:

```bash
# 1. Confirm provider is back to stub
python -c "from app.config import settings; assert settings.RUNTIME_PROVIDER == 'stub'"

# 2. Run all tests
pytest apps/api/tests -v

# 3. Verify no residual Docker containers
docker ps -a --filter name=opencode-smoke

# 4. Verify no residual worktree directories
ls .worktrees/

# 5. Check task_events for any unexpected event types
# (no runtime_session_created from real server, no deploy/* events)
```

## Risk Level

**HIGH** — requires explicit approval before execution.

Do NOT run this smoke test without:
1. Prior approval from project lead
2. Isolated environment (localhost only, no external network)
3. Confirmed `plan-only` mode on OpenCode server
4. Backup of current `.env` configuration
