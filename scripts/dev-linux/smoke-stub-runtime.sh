#!/usr/bin/env bash
# DEV-LINUX-01: Smoke test for stub runtime provider (plan-only).
# Creates project, agent, task. Calls POST /runtime/tasks/{id}/plan directly.
# Verifies approved status, stub-session session_id, plan_generated event.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

API_BASE="http://127.0.0.1:8000"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
PROJECT_SLUG="smoke-stub-$TIMESTAMP"
AGENT_SLUG="smoke-agent-$TIMESTAMP"

DRY_RUN=false

# ── helpers ─────────────────────────────────────────────────────────────

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Smoke test for stub runtime provider (plan-only).

Options:
  --dry-run     Validate preconditions only, print would-do actions
  --help        Show this help

Verifies:
  - API running in stub mode
  - Creates project, agent, low-risk task
  - POST /runtime/tasks/{id}/plan (direct, bypasses worker)
  - status=approved, session_id=stub-session, plan_generated=1
  - No runtime_error, policy_blocked, command/file/sandbox events
  - Git stays clean

Note: Worker bypass — direct POST /runtime used.
EOF
}

log_info()  { echo "[INFO] $*"; }
log_pass()  { echo "[PASS] $*"; }
log_fail()  { echo "[FAIL] $*"; }
log_dryrun(){ echo "[DRYRUN] would: $*"; }

exit_fail() {
    log_fail "$1"
    exit 1
}

api_post() {
    local url="$1"
    local body="$2"
    curl -sf -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "$body" \
        --max-time 120 2>/dev/null
}

api_get() {
    local url="$1"
    curl -sf "$url" --max-time 30 2>/dev/null
}

# ── parse args ──────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)  DRY_RUN=true; shift ;;
        --help)     usage; exit 0 ;;
        *)          echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

# ── preconditions ───────────────────────────────────────────────────────

# 1. API healthy
if ! curl -sf "$API_BASE/health" 2>/dev/null | grep -q '"ok"'; then
    exit_fail "API not healthy at $API_BASE"
fi
log_info "API healthy at $API_BASE"

# 2. Git clean
if [[ -n "$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null)" ]]; then
    exit_fail "Git working tree is dirty. Commit or stash before running smoke."
fi
log_info "Git status: clean"

# ── dry-run ─────────────────────────────────────────────────────────────

if $DRY_RUN; then
    echo ""
    echo "========== Smoke Stub Runtime DryRun =========="
    log_dryrun "verify API in stub mode"
    log_dryrun "verify git clean"
    log_dryrun "create project   slug=$PROJECT_SLUG"
    log_dryrun "create agent     slug=$AGENT_SLUG"
    log_dryrun "create task      risk_level=low"
    log_dryrun "POST /runtime/tasks/{id}/plan (timeout 120s)"
    log_dryrun "PRINT: Worker bypass: direct POST /runtime used."
    log_dryrun "verify status=approved"
    log_dryrun "verify session_id=stub-session"
    log_dryrun "verify plan_generated count=1"
    log_dryrun "verify no runtime_error, policy_blocked, command/file/sandbox events"
    log_dryrun "verify git still clean"
    echo "================================================"
    echo ""
    exit 0
fi

# ── create project ──────────────────────────────────────────────────────

log_info "Creating project '$PROJECT_SLUG' ..."
PROJECT_RESP=$(api_post "$API_BASE/projects" "{
    \"slug\": \"$PROJECT_SLUG\",
    \"name\": \"Smoke Stub Test $TIMESTAMP\",
    \"repo_path\": \"$PROJECT_ROOT\",
    \"memory_path\": \".ai_memory/projects/$PROJECT_SLUG\",
    \"default_branch\": \"main\",
    \"status\": \"active\",
    \"stack\": {\"framework\": \"fastapi\"}
}") || exit_fail "Failed to create project."

PROJECT_ID=$(echo "$PROJECT_RESP" | python -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
if [[ -z "$PROJECT_ID" ]]; then
    exit_fail "Failed to extract project ID from response."
fi
log_info "Project created: $PROJECT_ID"

# ── create agent ────────────────────────────────────────────────────────

log_info "Creating agent '$AGENT_SLUG' ..."
AGENT_RESP=$(api_post "$API_BASE/agents" "{
    \"slug\": \"$AGENT_SLUG\",
    \"name\": \"Smoke Agent $TIMESTAMP\",
    \"role\": \"smoke_tester\",
    \"system_prompt\": \"You are a smoke test agent. Plan only.\",
    \"model\": \"stub\",
    \"permissions\": {\"read_files\": true, \"write_files\": false},
    \"status\": \"active\"
}") || exit_fail "Failed to create agent."

AGENT_ID=$(echo "$AGENT_RESP" | python -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
if [[ -z "$AGENT_ID" ]]; then
    exit_fail "Failed to extract agent ID from response."
fi
log_info "Agent created: $AGENT_ID"

# ── create task ─────────────────────────────────────────────────────────

log_info "Creating task..."
TASK_RESP=$(api_post "$API_BASE/tasks" "{
    \"title\": \"Smoke stub test task\",
    \"raw_text\": \"Verify that the stub runtime correctly generates a plan.\",
    \"normalized_text\": \"Verify stub runtime plan generation\",
    \"risk_level\": \"low\",
    \"intent\": \"smoke_test\",
    \"project_id\": \"$PROJECT_ID\",
    \"agent_id\": \"$AGENT_ID\"
}") || exit_fail "Failed to create task."

TASK_ID=$(echo "$TASK_RESP" | python -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
TASK_STATUS=$(echo "$TASK_RESP" | python -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")
if [[ -z "$TASK_ID" ]]; then
    exit_fail "Failed to extract task ID from response."
fi
log_info "Task created: $TASK_ID (status: $TASK_STATUS)"

# ── call plan endpoint ──────────────────────────────────────────────────

echo ""
echo "**************************************************"
echo "* Worker bypass: direct POST /runtime used.      *"
echo "**************************************************"
echo ""

log_info "Calling POST /runtime/tasks/$TASK_ID/plan (timeout 120s)..."
PLAN_START=$(date +%s)
PLAN_RESP=$(api_post "$API_BASE/runtime/tasks/$TASK_ID/plan" "{}") || {
    exit_fail "Plan generation failed."
}
PLAN_END=$(date +%s)
PLAN_DURATION=$((PLAN_END - PLAN_START))
log_info "Plan endpoint returned in ${PLAN_DURATION}s"

# ── fetch updated task ──────────────────────────────────────────────────

log_info "Fetching updated task..."
UPDATED_TASK=$(api_get "$API_BASE/tasks/$TASK_ID") || exit_fail "Failed to fetch updated task."
TASK_STATUS_AFTER=$(echo "$UPDATED_TASK" | python -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")

# ── fetch task events ───────────────────────────────────────────────────

log_info "Fetching task events..."
EVENTS_RESP=$(api_get "$API_BASE/events/tasks/$TASK_ID/events" 2>/dev/null || echo '{"items":[]}')

# ── verifications ───────────────────────────────────────────────────────

# Parse with python for reliability
CHECKS=$(python3 -c "
import json, sys

task = json.loads('''$UPDATED_TASK''')
events_raw = '''$EVENTS_RESP'''
try:
    events = json.loads(events_raw)
    if isinstance(events, dict):
        event_list = events.get('items', events.get('events', [events]))
    elif isinstance(events, list):
        event_list = events
    else:
        event_list = [events]
except:
    event_list = []

checks = {
    'status_approved': task.get('status') == 'approved',
    'session_id_stub': False,
    'plan_generated': 0,
    'runtime_error': 0,
    'policy_blocked': 0,
    'command_started': 0,
    'file_changed': 0,
    'sandbox_events': 0,
}

# Check session_id in payload
payload = task.get('payload', {})
if isinstance(payload, str):
    try: payload = json.loads(payload)
    except: payload = {}
runtime_plan = payload.get('runtime_plan', {})
session_id = runtime_plan.get('session_id', '')
checks['session_id_stub'] = (session_id == 'stub-session')

# Count events
for evt in event_list:
    et = evt.get('event_type', '')
    if et == 'plan_generated': checks['plan_generated'] += 1
    if et == 'runtime_error': checks['runtime_error'] += 1
    if et == 'policy_blocked': checks['policy_blocked'] += 1
    if et == 'command_started': checks['command_started'] += 1
    if et == 'file_changed': checks['file_changed'] += 1
    if 'sandbox' in et: checks['sandbox_events'] += 1

print(json.dumps(checks))
" 2>/dev/null || echo '{}')

# Parse checks
STATUS_APPROVED=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('status_approved',False))" 2>/dev/null || echo "False")
SESSION_ID_STUB=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('session_id_stub',False))" 2>/dev/null || echo "False")
PLAN_GEN_COUNT=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('plan_generated',0))" 2>/dev/null || echo "0")
RUNTIME_ERR=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('runtime_error',0))" 2>/dev/null || echo "0")
POLICY_BLOCKED=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('policy_blocked',0))" 2>/dev/null || echo "0")
CMD_STARTED=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('command_started',0))" 2>/dev/null || echo "0")
FILE_CHANGED=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('file_changed',0))" 2>/dev/null || echo "0")
SANDBOX_EVENTS=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('sandbox_events',0))" 2>/dev/null || echo "0")

# Git check
GIT_AFTER=$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null || echo "")
GIT_CLEAN=true
[[ -n "$GIT_AFTER" ]] && GIT_CLEAN=false

# ── report ──────────────────────────────────────────────────────────────

pass_or_fail() { if [[ "$1" == "True" || "$1" == "0" || "$1" == "1" ]]; then echo "[PASS]"; else echo "[FAIL]"; fi }

echo ""
echo "========== Smoke Stub Runtime Report =========="
echo "  Task ID            : $TASK_ID"
echo "  Project slug       : $PROJECT_SLUG"
echo "  Agent slug         : $AGENT_SLUG"
echo "  Plan duration      : ${PLAN_DURATION}s"
echo ""
echo "  status=approved    : $(if [[ "$STATUS_APPROVED" == "True" ]]; then log_pass; else log_fail; fi)"
echo "  session_id=stub    : $(if [[ "$SESSION_ID_STUB" == "True" ]]; then log_pass; else log_fail; fi)"
echo "  plan_generated=1   : $(if [[ "$PLAN_GEN_COUNT" == "1" ]]; then log_pass; else log_fail "got: $PLAN_GEN_COUNT"; fi)"
echo "  no runtime_error   : $(if [[ "$RUNTIME_ERR" == "0" ]]; then log_pass; else log_fail "$RUNTIME_ERR"; fi)"
echo "  no policy_blocked  : $(if [[ "$POLICY_BLOCKED" == "0" ]]; then log_pass; else log_fail "$POLICY_BLOCKED"; fi)"
echo "  no command/file    : $(if [[ "$CMD_STARTED" == "0" && "$FILE_CHANGED" == "0" ]]; then log_pass; else log_fail; fi)"
echo "  no sandbox events  : $(if [[ "$SANDBOX_EVENTS" == "0" ]]; then log_pass; else log_fail; fi)"
echo "  git still clean    : $(if $GIT_CLEAN; then log_pass; else log_fail; fi)"
echo "================================================="
echo ""

ALL_PASSED=true
[[ "$STATUS_APPROVED" != "True" ]] && ALL_PASSED=false
[[ "$SESSION_ID_STUB" != "True" ]] && ALL_PASSED=false
[[ "$PLAN_GEN_COUNT" != "1" ]] && ALL_PASSED=false
[[ "$RUNTIME_ERR" != "0" ]] && ALL_PASSED=false
[[ "$POLICY_BLOCKED" != "0" ]] && ALL_PASSED=false
[[ "$CMD_STARTED" != "0" ]] && ALL_PASSED=false
[[ "$FILE_CHANGED" != "0" ]] && ALL_PASSED=false
[[ "$SANDBOX_EVENTS" != "0" ]] && ALL_PASSED=false
! $GIT_CLEAN && ALL_PASSED=false

if $ALL_PASSED; then
    log_pass "All smoke checks passed for stub runtime."
    exit 0
else
    log_fail "Some checks failed. Review report above."
    exit 1
fi
