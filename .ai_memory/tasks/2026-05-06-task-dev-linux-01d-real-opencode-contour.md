# Task Summary: DEV-LINUX-01D — Real OpenCode Runtime Contour on Linux

**Date:** 2026-05-06
**Task ID:** DEV-LINUX-01D
**Status:** ✅ COMPLETE
**Agent:** studio-orchestrator (coordinated execution)
**Contour:** local only; WSL2 Ubuntu 22.04; no deploy/migrations/.env/secrets

---

## Objective

Validate the real OpenCode runtime contour on Linux (WSL2 Ubuntu 22.04):
OpenCode server → API opencode_http → smoke-real-opencode-runtime → cleanup.

## Prerequisites

- DEV-LINUX-01C stub contour: PASS
- WSL2 Ubuntu 22.04 installed and running
- Docker Desktop WSL integration: amc-dev-postgres + amc-dev-redis healthy

## Results Summary

| Step | Result |
|------|--------|
| Step 0: WSL environment | ✅ Ubuntu 22.04.5 LTS, WSL2, repo at ~/agentrouter |
| Step 1: Prerequisites | ✅ Node v20.20.2, npm 10.8.2, OpenCode 1.14.39, Docker healthy |
| Step 2: bash -n syntax | ✅ 10/10 scripts OK |
| Step 3: check-db.sh | ✅ 9/9 tables, alembic head matches |
| Step 4: start-opencode.sh | ✅ PID 8570, 127.0.0.1:4096, /global/health 200, /doc 200 |
| Step 5: CLI attach probe | ✅ exit 0, ~42s, session ses_201ad1cf9ffeuGz8Ag5JiGQM0v |
| Step 6: start-api-opencode.sh | ✅ PID 9014, 127.0.0.1:8000, provider opencode_http, /health /projects /agents 200 |
| Step 7: smoke-real-opencode-runtime | ✅ task bc4853b6, approved, 103.2s, session ses_201a17dfcffem78R3kuE96eZPf, 2099 chars plan |
| Step 8: cleanup-runtime.sh | ✅ OpenCode stopped, API restarted stub, git clean |

## Detailed Results

### Environment
- **OS:** Ubuntu 22.04.5 LTS (Jammy) on WSL2
- **Kernel:** 6.6.87.2-microsoft-standard-WSL2
- **Arch:** x86_64
- **Node.js:** v20.20.2 (installed during this run via NodeSource)
- **npm:** 10.8.2
- **OpenCode:** 1.14.39 (installed from opencode-linux-x64 npm package)
- **Docker:** amc-dev-redis + amc-dev-postgres healthy

### OpenCode Server
- **PID:** 8570
- **Listen:** 127.0.0.1:4096
- **/global/health:** `{"healthy":true,"version":"1.14.39"}`
- **/doc:** OpenAPI 3.1.1
- **127.0.0.1 only:** YES

### CLI Attach Probe
- **Duration:** ~42s
- **Exit code:** 0
- **Session:** `ses_201ad1cf9ffeuGz8Ag5JiGQM0v` (real, not stub)
- **Action:** OpenCode read project directory structure via `read` tool
- **Git after:** Clean

### API opencode_http
- **PID:** 9014
- **Listen:** 127.0.0.1:8000
- **Provider:** opencode_http (process-scoped env, no .env changes)
- **/health /projects /agents:** All 200

### Real OpenCode Runtime Smoke
- **Task ID:** `bc4853b6-04f9-495a-9d02-0ea56a3c9cea`
- **Final status:** `approved`
- **Duration:** 103.2s
- **Session ID:** `ses_201a17dfcffem78R3kuE96eZPf` (real OpenCode format)
- **Plan length:** 2099 chars
- **Plan excerpt:** "I already completed a thorough analysis of the entire project... ~65% of MVP v1 complete. All core infrastructure is built and tested..."

**Event timeline:**
```
task_created
  → runtime_session_created (session=ses_201a17dfcffem78R3kuE96eZPf)
  → runtime_retry_scheduled (attempt=1)
  → runtime_event_received ×2
  → plan_generated
```

**Proof real OpenCode (not stub):**
- Session ID `ses_201a17dfcffem78R3kuE96eZPf` — real OpenCode format
- No stub fingerprints ("plan-only", "No code execution", "stub-session", "stub-agent")
- Plan content references actual project state
- Duration 103.2s (stub responds in <1s)

**Validation checks (all 9 PASS):**
1. ✅ final_status=approved
2. ✅ plan_text_nonempty (2099 chars)
3. ✅ real_session_id (ses_201a17dfcffem78R3kuE96eZPf)
4. ✅ plan_generated_count=1
5. ✅ session_created_before_events (rsc=1 < rer=3)
6. ✅ no_stub_fingerprints
7. ✅ no_runtime_error
8. ✅ no_policy_blocked
9. ✅ no_command_file_sandbox

### Cleanup
- OpenCode stopped (PID 8570)
- API stopped (PID 9014)
- API restarted in stub mode (PID 10056)
- Port 4096 free
- Port 8000 free (then stub restart)
- Git clean

## Findings

| # | Finding | Severity | Action |
|---|---------|----------|--------|
| 1 | First smoke attempt hit 420s timeout on cold-start | Medium | Manual retry succeeded in 103s; consider increasing script timeout |
| 2 | smoke-real-opencode-runtime.sh missing `normalized_text` field | Medium | Script needs update; manual fix applied |
| 3 | Node.js not installed in WSL | Low | Installed Node.js 20.20.2 via NodeSource |
| 4 | OpenCode npm package is platform-specific | Low | Used `opencode-linux-x64` + symlink to `/usr/local/bin/opencode` |

## Files Changed

- `.ai_memory/tasks/2026-05-06-task-dev-linux-01d-real-opencode-contour.md` (NEW)
- `PROJECT_MEMORY.md` (updated)
- `.ai_memory/current_state.md` (updated)

## Guardrails Intact

- ✅ No .env/secrets changed
- ✅ No migrations run
- ✅ No deploy
- ✅ No git push
- ✅ No port 3001
- ✅ No 0.0.0.0 binding
- ✅ No Telegram bot/messages
- ✅ Git clean after cleanup
- ✅ All services stopped, API restored to stub mode
