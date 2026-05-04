# OpenCode Smoke Test Procedure

> **Status:** plan-only document. Real OpenCode server has NOT been run.
> **Purpose:** checklist for a future controlled smoke test of the `RealOpenCodeHttpTransport` + real OpenCode server integration.

---

## Automated Alternative (BE-11)

**Use the BE-11 PowerShell scripts instead of following the manual procedure below.**

The scripts in `scripts/dev/` automate the full smoke test pipeline:

| Script | Purpose |
|--------|---------|
| `.\scripts\dev\smoke-stub-runtime.ps1` | Full stub smoke test (create → plan → 9 verification checks). All steps automated, no OpenCode server needed. |
| `.\scripts\dev\smoke-real-opencode-runtime.ps1` | Full real OpenCode E2E smoke test (create → plan → 13 verification checks). Requires OpenCode server healthy at `127.0.0.1:4096`. |
| `.\scripts\dev\start-opencode.ps1` | Start OpenCode server (`opencode serve --port 4096 --hostname 127.0.0.1`). Dynamic launcher detection. |
| `.\scripts\dev\start-api-opencode.ps1` | Start API with `opencode_http` provider, env overrides, config validation. |
| `.\scripts\dev\start-api-stub.ps1` | Start API with `stub` provider (default). |
| `.\scripts\dev\cleanup-runtime.ps1` | Stop OpenCode/Celery/API, auto-restart stub API, clean env. |

All scripts support `-DryRun` for safe pre-flight validation. See `docs/runtime-runbook.md` for the full runbook.

**The manual procedure below is kept as reference** for understanding each step and for environments where PowerShell scripts cannot be used.

---

## Pre-conditions

- [ ] `RUNTIME_PROVIDER=stub` confirmed (default)
- [ ] `OPENCODE_SERVER_URL` is empty or not set
- [ ] No production/staging servers involved
- [ ] Main project `.env` is NOT modified
- [ ] Docker sandbox mode is `fake` (not `docker`)
- [ ] `RUNTIME_ALLOW_REAL_OPENCODE_HTTP=false` by default is confirmed

## Smoke Test Steps

### Step 1: Start OpenCode server (BE-06 compatibility baseline)

Use **only** this command form:

```bash
opencode serve --port 4096 --hostname 127.0.0.1
```

Do **NOT** use:
- port `3001`
- `opencode/server`
- `@opencode/server`
- binding to `0.0.0.0`

Required identity endpoints for this procedure:
- `GET http://127.0.0.1:4096/global/health`
- `GET http://127.0.0.1:4096/doc`

### Step 2: Identity + compatibility preflight probes

Identity checks (must point to real OpenCode runtime):
- `GET /global/health` (required)
- `GET /doc` (required)

Compatibility note from backend:
- AMC runtime transport expects endpoints at `OPENCODE_SERVER_URL` root:
  - `POST /session`
  - `POST /session/{id}/message`
- `POST /session`:
  - **BE-08:** OpenCode 1.14.33 auto-detects workspace from CWD and IGNORES directory/cwd/path/workspace/mode/model.
    Only `title` field is accepted: `{"title": "<task title or 'Plan task'>"}`.
  - Response must include `session_id` or `id`
- Session timeout: **180s** (RUNTIME_SESSION_TIMEOUT_SECONDS, increased from 60s after BE-08 smoke showed insufficient)
- `POST /session/{id}/message` response must be JSON object with `parts` list
- Contract note (BE-07): request body for `POST /session/{id}/message` is aligned to confirmed shape:
  - `{"parts": [{"type": "text", "text": "<normalized task text>"}]}`
  - do NOT include unconfirmed fields for this endpoint (no: message, mode, correlation_id, idempotency_key, restrictions, capabilities)
- Response contract (BE-07): OpenCode 1.14.33 returns:
  - `{"info": {...}, "parts": [{"type":"step-start",...}, {"type":"reasoning","text":"..."}, {"type":"text","text":"## Plan..."}, {"type":"step-finish","reason":"stop"}]}`
  - `response["parts"]` is the required field (not `response["content"]`)
  - `part.type == "text"` → plan.delta (text content)
  - `part.type == "reasoning"` → SKIPPED (never saved to plan or events)
  - `part.type == "step-start"` → metadata-only, skipped
  - `part.type == "step-finish"` + `reason == "stop"` → plan.final
  - `part.type == "tool"` → tool.call (mutating actions blocked by policy)

Preflight probes (PowerShell examples):

```powershell
# 1) Identity
curl.exe -sS "http://127.0.0.1:4096/global/health"
curl.exe -sS "http://127.0.0.1:4096/doc"

# 2) Runtime endpoint probe: create session (BE-08: title-only payload)
$create = curl.exe -sS -X POST "http://127.0.0.1:4096/session" -H "Content-Type: application/json" -d "{\"title\":\"Smoke test probe\"}"
$obj = $create | ConvertFrom-Json
$sid = if ($obj.session_id) { $obj.session_id } elseif ($obj.id) { $obj.id } else { throw "No session_id/id in /session response" }

# 3) Runtime endpoint probe: sync message endpoint (BE-07 contract)
curl.exe -sS -X POST "http://127.0.0.1:4096/session/$sid/message" -H "Content-Type: application/json" -d "{\"parts\":[{\"type\":\"text\",\"text\":\"health probe\"}]}"
```

### Step 3: Configure AMC for opencode_http

Use temporary runtime overrides only (process env), **without editing any `.env` file**:

```powershell
# PowerShell example (current shell only)
$env:RUNTIME_PROVIDER="opencode_http"
$env:OPENCODE_SERVER_URL="http://127.0.0.1:4096"
$env:RUNTIME_ALLOW_REAL_OPENCODE_HTTP="true"
```

Do NOT create/edit `.env`, `.env.local`, or any alternate env file for this smoke procedure.

Restart the API server in the shell/session where overrides are set.

### Step 4: Run integration smoke test

Create a test task through the existing API or Telegram bot, then trigger plan generation:

```bash
# Example: POST /tasks then POST /runtime/tasks/{id}/plan
# Expected: task transitions to 'approved' (low risk) or 'waiting_approval' (medium/high)
# Expected: plan_text is populated, no 'runtime_error' events
```

### Step 5: Verify events

```bash
curl http://localhost:8000/events/tasks/{task_id}/events | python -m json.tool
```

Expected events (subset):
- `runtime_session_created` — session was created on OpenCode server
- `runtime_event_received` — at least one runtime event mapped from message parts
- `plan_generated` — plan was successfully generated
- No `runtime_timeout`, `runtime_error`, or `policy_blocked`

### Step 6: Cleanup

```powershell
# Stop OpenCode process (Ctrl+C in its terminal)

# Restore default runtime config (main .env remains unchanged)
Remove-Item Env:RUNTIME_PROVIDER -ErrorAction SilentlyContinue
Remove-Item Env:OPENCODE_SERVER_URL -ErrorAction SilentlyContinue
Remove-Item Env:RUNTIME_ALLOW_REAL_OPENCODE_HTTP -ErrorAction SilentlyContinue
```

**Verify defaults restored:**
- `RUNTIME_PROVIDER=stub`
- `OPENCODE_SERVER_URL=""`
- `RUNTIME_ALLOW_REAL_OPENCODE_HTTP=false`

## Abort Criteria

Stop the smoke test immediately if any of the following occurs:

1. **real code execution triggered** — any command actually runs (check task events for `command_started`, `command_finished`, `file_changed`)
2. **network escape** — OpenCode server attempts outbound connections beyond localhost
3. **file system writes** — any files modified outside `.worktrees/`
4. **secrets leaked** — any `.env`, token, or key appears in plan_text or task_events
5. **approval bypass** — medium/high/critical task transitions to `approved` without explicit approval
6. **provider fallback** — `runtime_error` occurs because OpenCode server is unreachable but task falls back to stub (Must NOT happen)

## Post-Smoke Checks

After cleanup, verify:

```bash
# 1. Confirm runtime defaults are back
python -c "from app.config import settings; assert settings.RUNTIME_PROVIDER == 'stub'; assert settings.OPENCODE_SERVER_URL == ''; assert settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP is False"
```

## Risk Level

**HIGH** — requires explicit approval before execution.

Do NOT run this smoke test without:
1. Prior approval from project lead
2. Isolated environment (localhost only, no external network)
3. Confirmed `plan-only` mode on OpenCode server
4. Confirmation that main `.env` will not be edited
