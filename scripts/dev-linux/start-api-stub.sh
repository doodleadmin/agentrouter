#!/usr/bin/env bash
# DEV-LINUX-01: Start API server in stub runtime mode.
# Starts FastAPI orchestrator with default/stub provider on 127.0.0.1:8000.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Auto-detect Python venv
if [[ -d "$PROJECT_ROOT/.venv/bin" ]]; then
    export PATH="$PROJECT_ROOT/.venv/bin:$PATH"
fi

API_DIR="$PROJECT_ROOT/apps/api"
PORT="${PORT:-8000}"
HEALTH_URL="http://127.0.0.1:${PORT}/health"
PROJECTS_URL="http://127.0.0.1:${PORT}/projects"
AGENTS_URL="http://127.0.0.1:${PORT}/agents"
LOG_DIR="$PROJECT_ROOT/logs/dev"
LOG_FILE="$LOG_DIR/api-stub.log"
PID_DIR="$PROJECT_ROOT/.runtime"
PID_FILE="$PID_DIR/api.pid"
VERIFY_RETRIES=15
VERIFY_DELAY=0.5

DRY_RUN=false

# ── helpers ─────────────────────────────────────────────────────────────

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Start API server in stub runtime mode on 127.0.0.1:${PORT}.

Options:
  --port PORT   Port to listen on (default: 8000)
  --dry-run     Validate preconditions only, print would-do actions
  --help        Show this help

Environment (process-scoped, never persisted):
  DEBUG=true    Enable debug mode (default for dev)

Logs: $LOG_FILE
PID:  $PID_FILE
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

is_port_in_use() {
    local port="$1"
    ss -tlnp 2>/dev/null | grep -q ":${port} " && return 0 || return 1
}

is_process_alive() {
    local pid="$1"
    kill -0 "$pid" 2>/dev/null
}

# ── parse args ──────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --port)     PORT="$2"; shift 2 ;;
        --dry-run)  DRY_RUN=true; shift ;;
        --help)     usage; exit 0 ;;
        *)          echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

# Update URLs after arg parsing
HEALTH_URL="http://127.0.0.1:${PORT}/health"
PROJECTS_URL="http://127.0.0.1:${PORT}/projects"
AGENTS_URL="http://127.0.0.1:${PORT}/agents"

# ── preconditions ───────────────────────────────────────────────────────

# 1. DB bootstrapped
if docker inspect --format='{{.State.Status}}' amc-dev-postgres 2>/dev/null | grep -q running; then
    ALEMBIC_EXISTS=$(docker exec amc-dev-postgres psql -U agent_mc -d agent_mc -tAc \
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')" 2>/dev/null || echo "f")
    ALEMBIC_EXISTS=$(echo "$ALEMBIC_EXISTS" | tr -d '[:space:]')
    if [[ "$ALEMBIC_EXISTS" != "t" ]]; then
        exit_fail "Database not bootstrapped. Run bootstrap-db.sh first."
    fi
fi

# 2. uvicorn installed
if ! python -c "import uvicorn" 2>/dev/null; then
    exit_fail "uvicorn is not installed. Install with: pip install uvicorn"
fi

# ── dry-run ─────────────────────────────────────────────────────────────

if $DRY_RUN; then
    echo ""
    echo "========== Start API Stub DryRun =========="
    log_dryrun "remove existing RUNTIME env overrides from process"
    log_dryrun "set process-scoped DEBUG=true"
    log_dryrun "source .env.local if present (CALLBACK_SECRET, etc.)"
    log_dryrun "start uvicorn on 127.0.0.1:$PORT (provider: stub)"
    log_dryrun "verify $HEALTH_URL -> 200"
    log_dryrun "verify $PROJECTS_URL -> 200"
    log_dryrun "verify $AGENTS_URL -> 200"
    echo "============================================="
    echo ""
    exit 0
fi

# ── check if already running ────────────────────────────────────────────

if [[ -f "$PID_FILE" ]]; then
    OLD_PID=$(cat "$PID_FILE")
    if is_process_alive "$OLD_PID"; then
        # Check if it's actually our API
        CMDLINE=$(cat "/proc/$OLD_PID/cmdline" 2>/dev/null | tr '\0' ' ' || echo "")
        if echo "$CMDLINE" | grep -q "app.main:app"; then
            log_info "API already running. PID: $OLD_PID"
            # Quick health check
            if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
                echo ""
                echo "========== Start API Stub Report =========="
                echo "  Status     : ALREADY_RUNNING"
                echo "  PID        : $OLD_PID"
                echo "  Listen     : 127.0.0.1:$PORT"
                echo "  Provider   : stub"
                echo "  /health    : 200 OK"
                echo "============================================="
                echo ""
                exit 0
            fi
        fi
    fi
    # Stale PID file
    rm -f "$PID_FILE"
fi

# ── start API ───────────────────────────────────────────────────────────

mkdir -p "$LOG_DIR" "$PID_DIR"

# Clean runtime env overrides
unset RUNTIME_PROVIDER OPENCODE_SERVER_URL RUNTIME_ALLOW_REAL_OPENCODE_HTTP API_TIMEOUT_SECONDS 2>/dev/null || true
# DEBUG enables app debug behavior (FastAPI error detail etc).
# SQL_ECHO intentionally remains unset/false — SQLAlchemy echo logs bind params.
# For temporary local SQL debugging only, run with SQL_ECHO=true explicitly.
export DEBUG="true"

# ── source .env.local (process-scoped, never persisted) ──────────────────
# INFRA-01: Load CALLBACK_SECRET and other secrets from .env.local.
# API's pydantic-settings reads from process env (overrides file defaults).
ENV_LOCAL="$PROJECT_ROOT/.env.local"
if [[ -f "$ENV_LOCAL" ]]; then
    set -a
    source "$ENV_LOCAL"
    set +a
    if [[ -n "${CALLBACK_SECRET:-}" ]]; then
        log_info "CALLBACK_SECRET: set (not displayed)"
    else
        log_warn "CALLBACK_SECRET not set in .env.local — callback validation will fail"
    fi
else
    log_warn ".env.local not found — callback validation will fail"
fi

log_info "Starting API in stub mode on 127.0.0.1:$PORT ..."
log_info "Provider mode: stub (default)"

cd "$PROJECT_ROOT"
nohup python -m uvicorn --app-dir "$API_DIR" app.main:app \
    --host 127.0.0.1 --port "$PORT" \
    > "$LOG_FILE" 2>&1 &

API_PID=$!
echo "$API_PID" > "$PID_FILE"
log_info "API process started. PID: $API_PID"
log_info "Listen address: 127.0.0.1:$PORT"
log_info "Log file: $LOG_FILE"

# ── verify endpoints ────────────────────────────────────────────────────

log_info "Verifying API endpoints..."
HEALTH_OK=false
PROJECTS_OK=false
AGENTS_OK=false

for ((i=1; i<=VERIFY_RETRIES; i++)); do
    sleep "$VERIFY_DELAY"

    if ! $HEALTH_OK; then
        if curl -sf "$HEALTH_URL" 2>/dev/null | grep -q '"ok"'; then
            HEALTH_OK=true
        fi
    fi

    if $HEALTH_OK; then
        HTTP_CODE=$(curl -sf -o /dev/null -w '%{http_code}' "$PROJECTS_URL" 2>/dev/null || echo "000")
        [[ "$HTTP_CODE" == "200" ]] && PROJECTS_OK=true

        HTTP_CODE=$(curl -sf -o /dev/null -w '%{http_code}' "$AGENTS_URL" 2>/dev/null || echo "000")
        [[ "$HTTP_CODE" == "200" ]] && AGENTS_OK=true

        if $PROJECTS_OK && $AGENTS_OK; then
            break
        fi
    fi
done

# ── report ──────────────────────────────────────────────────────────────

echo ""
echo "========== Start API Stub Report =========="
echo "  PID          : $API_PID"
echo "  Listen       : 127.0.0.1:$PORT"
echo "  Provider     : stub"
  echo "  /health      : $(if $HEALTH_OK; then echo '200 OK'; else echo 'FAIL'; fi)"
  echo "  /projects    : $(if $PROJECTS_OK; then echo '200 OK'; else echo 'FAIL'; fi)"
  echo "  /agents      : $(if $AGENTS_OK; then echo '200 OK'; else echo 'FAIL'; fi)"
  echo "  CALLBACK_SECRET : $(if [[ -n "${CALLBACK_SECRET:-}" ]]; then echo 'set (not displayed)'; else echo '(empty — callbacks will fail)'; fi)"
  echo "  DATABASE_URL : $(if [[ -n "${DATABASE_URL:-}" ]]; then echo 'set (from env)'; else echo '(using config default)'; fi)"
  echo "  Log file     : $LOG_FILE"
echo "============================================="
echo ""

if ! $HEALTH_OK || ! $PROJECTS_OK || ! $AGENTS_OK; then
    log_warn "Some endpoints did not return 200 within timeout."
    log_warn "Check if DB is properly bootstrapped and accessible."
    log_warn "See log: $LOG_FILE"
fi

exit 0
