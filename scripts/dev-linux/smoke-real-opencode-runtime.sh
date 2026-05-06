#!/usr/bin/env bash
# DEV-LINUX-01: Smoke test for real OpenCode runtime provider.
# Verifies opencode_http runtime with a real OpenCode server.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

API_BASE="http://127.0.0.1:8000"
OPENCODE_BASE="http://127.0.0.1:4096"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
PROJECT_SLUG="smoke-real-$TIMESTAMP"
AGENT_SLUG="smoke-agent-$TIMESTAMP"
TIMEOUT_SECONDS="${TIMEOUT:-360}"

STUB_FINGERPRINTS=(
    "stub-session"
    "## Safety"
    "## Task Context"
    "No code execution"
    "No file modifications"
)

SECRET_PATTERNS=(
    '(api[_-]?key|token|secret|password|passwd)\s*[:=]\s*\S+'
    'sk-[A-Za-z0-9]{20,}'
    'ghp_[A-Za-z0-9]{20,}'
    'Bearer\s+[A-Za-z0-9\-_\.]{20,}'
)

DRY_RUN=false

# ── helpers ─────────────────────────────────────────────────────────────

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Smoke test for real OpenCode runtime provider.

Options:
  --timeout SEC   Max time to wait for plan generation (default: 360)
  --dry-run       Validate preconditions only, print would-do actions
  --help          Show this help

Requires:
  - OpenCode healthy at $OPENCODE_BASE
  - API running in opencode_http mode at $API_BASE

Verifies:
  - session_id starts with 'ses_' (not stub)
  - No stub fingerprints in plan_text
  - Event ordering: runtime_session_created before runtime_event_received
  - plan_generated=1, no errors/timeouts/policy blocks
  - No reasoning/secret leak
  - Git unchanged vs baseline
EOF
}

log_info()  { echo "[INFO] $*"; }
log_pass()  { echo "[PASS] $*"; }
log_fail()  { echo "[FAIL] $*"; }
log_warn()  { echo "[WARN] $*"; }
log_dryrun(){ echo "[DRYRUN] would: $*"; }

exit_fail() {
    log_fail "$1"
    exit 1
}

api_post() {
    local url="$1"
    local body="$2"
    local timeout="${3:-30}"
    curl -sf -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "$body" \
        --max-time "$timeout" 2>/dev/null
}

api_patch() {
    local url="$1"
    local body="$2"
    curl -sf -X PATCH "$url" \
        -H "Content-Type: application/json" \
        -d "$body" \
        --max-time 30 2>/dev/null
}

api_get() {
    local url="$1"
    curl -sf "$url" --max-time 30 2>/dev/null
}

# ── parse args ──────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --timeout)  TIMEOUT_SECONDS="$2"; shift 2 ;;
        --dry-run)  DRY_RUN=true; shift ;;
        --help)     usage; exit 0 ;;
        *)          echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

# ── preconditions ───────────────────────────────────────────────────────

if ! $DRY_RUN; then
    # 1. OpenCode healthy
    if ! curl -sf "$OPENCODE_BASE/global/health" >/dev/null 2>&1; then
        exit_fail "OpenCode not healthy at $OPENCODE_BASE. Run start-opencode.sh first."
    fi
    log_info "OpenCode healthy at $OPENCODE_BASE"

    # 2. API healthy
    if ! curl -sf "$API_BASE/health" 2>/dev/null | grep -q '"ok"'; then
        exit_fail "API not healthy at $API_BASE. Run start-api-opencode.sh first."
    fi
    log_info "API healthy at $API_BASE"

    # 3. Git baseline
    GIT_BEFORE=$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null || echo "")
    log_info "Git status baseline captured."
fi

# ── dry-run ─────────────────────────────────────────────────────────────

if $DRY_RUN; then
    echo ""
    echo "========== Smoke Real OpenCode Runtime DryRun =========="
    log_dryrun "verify API in opencode_http mode"
    log_dryrun "verify OpenCode healthy at $OPENCODE_BASE"
    log_dryrun "verify git clean"
    log_dryrun "PRINT: Worker bypass: direct POST /runtime used"
    log_dryrun "create project   slug=$PROJECT_SLUG"
    log_dryrun "create agent     slug=$AGENT_SLUG"
    log_dryrun "create task      risk_level=low"
    log_dryrun "POST /runtime/tasks/{id}/plan (timeout ${TIMEOUT_SECONDS}s)"
    log_dryrun "verify session_id starts with 'ses_'"
    log_dryrun "verify no stub fingerprints in plan_text"
    log_dryrun "verify no reasoning/secret leak"
    log_dryrun "verify git unchanged vs baseline"
    echo "========================================================="
    echo ""
    exit 0
fi

# ── create project ──────────────────────────────────────────────────────

log_info "Creating project '$PROJECT_SLUG' ..."
PROJECT_RESP=$(api_post "$API_BASE/projects" "{
    \"slug\": \"$PROJECT_SLUG\",
    \"name\": \"Smoke Real OpenCode Test $TIMESTAMP\",
    \"repo_path\": \"$PROJECT_ROOT\",
    \"memory_path\": \".ai_memory/projects/$PROJECT_SLUG\",
    \"default_branch\": \"main\",
    \"status\": \"active\",
    \"stack\": {\"framework\": \"fastapi\"}
}") || exit_fail "Failed to create project."

PROJECT_ID=$(echo "$PROJECT_RESP" | python -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
[[ -z "$PROJECT_ID" ]] && exit_fail "Failed to extract project ID."
log_info "Project created: $PROJECT_ID"

# ── create agent ────────────────────────────────────────────────────────

log_info "Creating agent '$AGENT_SLUG' ..."
AGENT_RESP=$(api_post "$API_BASE/agents" "{
    \"slug\": \"$AGENT_SLUG\",
    \"name\": \"Smoke Agent $TIMESTAMP\",
    \"role\": \"smoke_tester\",
    \"system_prompt\": \"You are a smoke test agent. Generate plan only.\",
    \"model\": \"opencode\",
    \"permissions\": {\"read_files\": true, \"write_files\": false},
    \"status\": \"active\"
}") || exit_fail "Failed to create agent."

AGENT_ID=$(echo "$AGENT_RESP" | python -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
[[ -z "$AGENT_ID" ]] && exit_fail "Failed to extract agent ID."
log_info "Agent created: $AGENT_ID"

# ── create task ─────────────────────────────────────────────────────────

log_info "Creating task..."
TASK_RESP=$(api_post "$API_BASE/tasks" "{
    \"title\": \"Smoke real OpenCode test task\",
    \"raw_text\": \"Look at the project structure and propose a plan for adding a /version endpoint to the API.\",
    \"normalized_text\": \"Propose a plan for adding a /version endpoint to the FastAPI application\",
    \"risk_level\": \"low\",
    \"intent\": \"smoke_test\",
    \"project_id\": \"$PROJECT_ID\",
    \"agent_id\": \"$AGENT_ID\"
}") || exit_fail "Failed to create task."

TASK_ID=$(echo "$TASK_RESP" | python -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
[[ -z "$TASK_ID" ]] && exit_fail "Failed to extract task ID."
log_info "Task created: $TASK_ID"

# ── route task ──────────────────────────────────────────────────────────

log_info "Preparing task for planning..."
api_patch "$API_BASE/tasks/$TASK_ID/status" '{"status":"routed"}' >/dev/null 2>&1 || log_warn "Could not set routed status."

# ── call plan endpoint ──────────────────────────────────────────────────

echo ""
echo "**************************************************"
echo "* Worker bypass: direct POST /runtime used.      *"
echo "**************************************************"
echo ""

RUNTIME_TIMEOUT=$((TIMEOUT_SECONDS > 420 ? TIMEOUT_SECONDS : 420))
log_info "Calling runtime plan endpoint (timeout ${RUNTIME_TIMEOUT}s)..."
PLAN_START=$(date +%s)

# Use curl with longer timeout for real OpenCode
PLAN_RESP=$(curl -sf -X POST "$API_BASE/runtime/tasks/$TASK_ID/plan" \
    -H "Content-Type: application/json" \
    -d '{}' \
    --max-time "$RUNTIME_TIMEOUT" 2>/dev/null) || {
    log_warn "Plan POST failed. Checking task state..."
    api_get "$API_BASE/tasks/$TASK_ID" >/dev/null 2>&1 || true
    exit_fail "Plan generation failed."
}

PLAN_END=$(date +%s)
PLAN_DURATION=$((PLAN_END - PLAN_START))
log_info "Plan endpoint returned in ${PLAN_DURATION}s"

# ── fetch updated task + events ─────────────────────────────────────────

log_info "Fetching updated task..."
UPDATED_TASK=$(api_get "$API_BASE/tasks/$TASK_ID") || exit_fail "Failed to fetch updated task."

log_info "Fetching task events..."
EVENTS_RESP=$(api_get "$API_BASE/task-events?task_id=$TASK_ID" 2>/dev/null || echo '{"items":[]}')

# ── verifications ───────────────────────────────────────────────────────

# Build stub fingerprints as JSON array
STUB_FP_JSON=$(printf '%s\n' "${STUB_FINGERPRINTS[@]}" | python -c "import sys,json; print(json.dumps([l.strip() for l in sys.stdin]))" 2>/dev/null || echo '[]')
SECRET_PAT_JSON=$(printf '%s\n' "${SECRET_PATTERNS[@]}" | python -c "import sys,json; print(json.dumps([l.strip() for l in sys.stdin]))" 2>/dev/null || echo '[]')

CHECKS=$(python3 -c "
import json, sys, re

task_json = '''$UPDATED_TASK'''
events_json = '''$EVENTS_RESP'''
stub_fps = json.loads('''$STUB_FP_JSON''')
secret_pats = json.loads('''$SECRET_PAT_JSON''')

task = json.loads(task_json)
try:
    events = json.loads(events_json)
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
    'session_id_valid': False,
    'no_stub_fingerprints': True,
    'event_order_correct': False,
    'plan_generated': 0,
    'runtime_error': 0,
    'runtime_timeout': 0,
    'policy_blocked': 0,
    'command_started': 0,
    'command_finished': 0,
    'file_changed': 0,
    'sandbox_events': 0,
    'reasoning_leak': False,
    'secret_leak': False,
}

# Session ID
payload = task.get('payload', {})
if isinstance(payload, str):
    try: payload = json.loads(payload)
    except: payload = {}
runtime_plan = payload.get('runtime_plan', {})
session_id = runtime_plan.get('session_id', '')
checks['session_id_valid'] = (
    session_id != '' and
    session_id != 'stub-session' and
    session_id.startswith('ses_')
)

# Plan text
plan_text = task.get('plan_text', '') or ''

# Stub fingerprints
for fp in stub_fps:
    if fp in plan_text:
        checks['no_stub_fingerprints'] = False
        break

# Event ordering
session_created_idx = -1
first_event_recv_idx = -1
for i, evt in enumerate(event_list):
    et = evt.get('event_type', '')
    if et == 'runtime_session_created' and session_created_idx < 0:
        session_created_idx = i
    if et == 'runtime_event_received' and first_event_recv_idx < 0:
        first_event_recv_idx = i
checks['event_order_correct'] = (
    session_created_idx >= 0 and
    first_event_recv_idx >= 0 and
    session_created_idx < first_event_recv_idx
)

# Count events
for evt in event_list:
    et = evt.get('event_type', '')
    if et == 'plan_generated': checks['plan_generated'] += 1
    if et == 'runtime_error': checks['runtime_error'] += 1
    if et == 'runtime_timeout': checks['runtime_timeout'] += 1
    if et == 'policy_blocked': checks['policy_blocked'] += 1
    if et == 'command_started': checks['command_started'] += 1
    if et == 'command_finished': checks['command_finished'] += 1
    if et == 'file_changed': checks['file_changed'] += 1
    if 'sandbox' in et: checks['sandbox_events'] += 1

# Reasoning leak
reasoning_markers = ['[REASONING]', '[Internal]', '<thinking>', 'let me think', 'let me reason', 'my reasoning']
for marker in reasoning_markers:
    if marker.lower() in plan_text.lower():
        checks['reasoning_leak'] = True
        break

# Secret leak
for pat in secret_pats:
    if re.search(pat, plan_text, re.IGNORECASE):
        checks['secret_leak'] = True
        break

checks['plan_length'] = len(plan_text)
checks['session_id'] = session_id

print(json.dumps(checks))
" 2>/dev/null || echo '{}')

# Parse results
STATUS_APPROVED=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('status_approved',False))" 2>/dev/null || echo "False")
SESSION_ID_VALID=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('session_id_valid',False))" 2>/dev/null || echo "False")
SESSION_ID=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('session_id',''))" 2>/dev/null || echo "")
NO_STUB_FP=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('no_stub_fingerprints',False))" 2>/dev/null || echo "False")
EVENT_ORDER=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('event_order_correct',False))" 2>/dev/null || echo "False")
PLAN_GEN=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('plan_generated',0))" 2>/dev/null || echo "0")
RT_ERROR=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('runtime_error',0))" 2>/dev/null || echo "0")
RT_TIMEOUT=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('runtime_timeout',0))" 2>/dev/null || echo "0")
POLICY_BLK=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('policy_blocked',0))" 2>/dev/null || echo "0")
CMD_START=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('command_started',0))" 2>/dev/null || echo "0")
CMD_FINISH=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('command_finished',0))" 2>/dev/null || echo "0")
FILE_CHG=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('file_changed',0))" 2>/dev/null || echo "0")
SANDBOX_EV=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('sandbox_events',0))" 2>/dev/null || echo "0")
REASON_LEAK=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('reasoning_leak',False))" 2>/dev/null || echo "False")
SECRET_LEAK=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('secret_leak',False))" 2>/dev/null || echo "False")
PLAN_LEN=$(echo "$CHECKS" | python -c "import sys,json; print(json.load(sys.stdin).get('plan_length',0))" 2>/dev/null || echo "0")

GIT_AFTER=$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null || echo "")
GIT_UNCHANGED=true
[[ "$GIT_AFTER" != "$GIT_BEFORE" ]] && GIT_UNCHANGED=false

# ── report ──────────────────────────────────────────────────────────────

pf() { if [[ "$1" == "True" || "$1" == "0" ]]; then echo "[PASS]"; else echo "[FAIL]"; fi }

echo ""
echo "========== Smoke Real OpenCode Runtime Report =========="
echo "  Task ID            : $TASK_ID"
echo "  Worker bypass      : direct POST /runtime used."
echo "  Session ID         : $SESSION_ID"
echo "  Plan length        : $PLAN_LEN chars"
echo "  Duration           : ${PLAN_DURATION}s"
echo "  Project slug       : $PROJECT_SLUG"
echo "  Agent slug         : $AGENT_SLUG"
echo ""
echo "  status=approved              : $(pf "$STATUS_APPROVED")"
echo "  session_id ~ 'ses_'          : $(pf "$SESSION_ID_VALID")"
echo "  no stub fingerprints         : $(pf "$NO_STUB_FP")"
echo "  event order (create < recv)  : $(pf "$EVENT_ORDER")"
echo "  plan_generated=1             : $(if [[ "$PLAN_GEN" == "1" ]]; then log_pass; else log_fail "($PLAN_GEN)"; fi)"
echo "  no runtime_error             : $(pf "$RT_ERROR")"
echo "  no runtime_timeout           : $(pf "$RT_TIMEOUT")"
echo "  no policy_blocked            : $(pf "$POLICY_BLK")"
echo "  no command/file events       : $(if [[ "$CMD_START" == "0" && "$CMD_FINISH" == "0" && "$FILE_CHG" == "0" ]]; then log_pass; else log_fail; fi)"
echo "  no sandbox events            : $(pf "$SANDBOX_EV")"
echo "  no reasoning leak            : $(if [[ "$REASON_LEAK" == "False" ]]; then log_pass; else log_fail; fi)"
echo "  no secret leak               : $(if [[ "$SECRET_LEAK" == "False" ]]; then log_pass; else log_fail; fi)"
echo "  git unchanged vs baseline    : $(if $GIT_UNCHANGED; then log_pass; else log_fail; fi)"
echo "========================================================="
echo ""

ALL_PASSED=true
for val in "$STATUS_APPROVED" "$SESSION_ID_VALID" "$NO_STUB_FP" "$EVENT_ORDER"; do
    [[ "$val" != "True" ]] && ALL_PASSED=false
done
[[ "$PLAN_GEN" != "1" ]] && ALL_PASSED=false
for val in "$RT_ERROR" "$RT_TIMEOUT" "$POLICY_BLK" "$CMD_START" "$CMD_FINISH" "$FILE_CHG" "$SANDBOX_EV"; do
    [[ "$val" != "0" ]] && ALL_PASSED=false
done
[[ "$REASON_LEAK" != "False" ]] && ALL_PASSED=false
[[ "$SECRET_LEAK" != "False" ]] && ALL_PASSED=false
! $GIT_UNCHANGED && ALL_PASSED=false

if $ALL_PASSED; then
    log_pass "All smoke checks passed for real OpenCode runtime."
    exit 0
else
    log_fail "Some checks failed. Review report above."
    exit 1
fi
