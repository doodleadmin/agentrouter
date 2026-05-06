#!/usr/bin/env bash
# DEV-LINUX-01: Start API server in opencode_http runtime mode.
# Requires OpenCode server to be healthy first.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Auto-detect Python venv
if [[ -d "$PROJECT_ROOT/.venv/bin" ]]; then
    export PATH="$PROJECT_ROOT/.venv/bin:$PATH"
fi

API_DIR="$PROJECT_ROOT/apps/api"
PORT="${PORT:-8000}"
OPENCODE_URL="${OPENCODE_URL:-http://127.0.0.1:4096}"
HEALTH_URL="http://127.0.0.1:${PORT}/health"
PROJECTS_URL="http://127.0.0.1:${PORT}/projects"
AGENTS_URL="http://127.0.0.1:${PORT}/agents"
OPENCODE_HEALTH_URL="${OPENCODE_URL}/global/health"
OPENCODE_DOC_URL="${OPENCODE_URL}/doc"
LOG_DIR="$PROJECT_ROOT/logs/dev"
LOG_FILE="$LOG_DIR/api-opencode.log"
PID_DIR="$PROJECT_ROOT/.runtime"
PID_FILE="$PID_DIR/api.pid"
VERIFY_RETRIES=40
VERIFY_DELAY=0.75

DRY_RUN=false

# ── helpers ─────────────────────────────────────────────────────────────

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Start API server in opencode_http runtime mode on 127.0.0.1:${PORT}.

Options:
  --port PORT           API port (default: 8000)
  --opencode-url URL    OpenCode server URL (default: http://127.0.0.1:4096)
  --dry-run             Validate preconditions only, print would-do actions
  --help                Show this help

Requires: OpenCode server healthy at <opencode-url>

Environment (process-scoped, never persisted):
  RUNTIME_PROVIDER=opencode_http
  OPENCODE_SERVER_URL=<opencode-url>
  RUNTIME_ALLOW_REAL_OPENCODE_HTTP=true
  DEBUG=true

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

is_process_alive() {
    local pid="$1"
    kill -0 "$pid" 2>/dev/null
}

stop_api_on_port() {
    local port="$1"
    local pids
    pids=$(ss -tlnp 2>/dev/null | grep ":${port} " | grep -oP 'pid=\K[0-9]+' | sort -u || true)
    for pid in $pids; do
        local cmd
        cmd=$(cat "/proc/$pid/cmdline" 2>/dev/null | tr '\0' ' ' || echo "")
        if echo "$cmd" | grep -q "app.main:app"; then
            log_info "Stopping existing API process (PID $pid) on port $port ..."
            kill "$pid" 2>/dev/null || true
            sleep 1
        fi
    done
}

# ── parse args ──────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --port)           PORT="$2"; shift 2 ;;
        --opencode-url)   OPENCODE_URL="$2"; shift 2 ;;
        --dry-run)        DRY_RUN=true; shift ;;
        --help)           usage; exit 0 ;;
        *)                echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

HEALTH_URL="http://127.0.0.1:${PORT}/health"
PROJECTS_URL="http://127.0.0.1:${PORT}/projects"
AGENTS_URL="http://127.0.0.1:${PORT}/agents"
OPENCODE_HEALTH_URL="${OPENCODE_URL}/global/health"
OPENCODE_DOC_URL="${OPENCODE_URL}/doc"

# ── preconditions ───────────────────────────────────────────────────────

if ! $DRY_RUN; then
    # 1. OpenCode healthy
    if ! curl -sf "$OPENCODE_HEALTH_URL" >/dev/null 2>&1; then
        exit_fail "OpenCode not healthy at $OPENCODE_URL. Run start-opencode.sh first."
    fi
    log_info "OpenCode healthy at $OPENCODE_URL"

    # 2. uvicorn installed
    if ! python -c "import uvicorn" 2>/dev/null; then
        exit_fail "uvicorn is not installed."
    fi
fi

# ── fast-path: already running in opencode_http mode ────────────────────

if ! $DRY_RUN; then
    if [[ -f "$PID_FILE" ]]; then
        OLD_PID=$(cat "$PID_FILE")
        if is_process_alive "$OLD_PID"; then
            CMDLINE=$(cat "/proc/$OLD_PID/cmdline" 2>/dev/null | tr '\0' ' ' || echo "")
            if echo "$CMDLINE" | grep -q "app.main:app"; then
                if curl -sf "$HEALTH_URL" 2>/dev/null | grep -q '"ok"'; then
                    echo ""
                    echo "========== Start API OpenCode Report =========="
                    echo "  Status       : ALREADY_RUNNING"
                    echo "  PID          : $OLD_PID"
                    echo "  Listen       : 127.0.0.1:$PORT"
                    echo "  Provider     : opencode_http"
                    echo "  /health      : 200 OK"
                    echo "==============================================="
                    echo ""
                    exit 0
                fi
            fi
        fi
        rm -f "$PID_FILE"
    fi
fi

# ── dry-run ─────────────────────────────────────────────────────────────

if $DRY_RUN; then
    echo ""
    echo "========== Start API OpenCode DryRun =========="
    log_dryrun "verify OpenCode /global/health and /doc at $OPENCODE_URL"
    log_dryrun "stop existing AMC API on port $PORT"
    log_dryrun "set process-scoped env:"
    echo "    RUNTIME_PROVIDER=opencode_http"
    echo "    OPENCODE_SERVER_URL=$OPENCODE_URL"
    echo "    RUNTIME_ALLOW_REAL_OPENCODE_HTTP=true"
    echo "    DEBUG=true"
    log_dryrun "launch uvicorn on 127.0.0.1:$PORT"
    log_dryrun "redirect stdout -> $LOG_FILE"
    log_dryrun "poll /health, /projects, /agents up to 30s"
    log_dryrun "verify listener 127.0.0.1 only"
    log_dryrun "NOT set DATABASE_URL"
    echo "================================================="
    echo ""
    exit 0
fi

# ── stop existing API ───────────────────────────────────────────────────

stop_api_on_port "$PORT"
sleep 0.5

# Verify port free
if ss -tlnp 2>/dev/null | grep -q ":${PORT} "; then
    exit_fail "Port $PORT on 127.0.0.1 is still occupied. Cannot start API."
fi

# ── set process-scoped env ──────────────────────────────────────────────

export RUNTIME_PROVIDER="opencode_http"
export OPENCODE_SERVER_URL="$OPENCODE_URL"
export RUNTIME_ALLOW_REAL_OPENCODE_HTTP="true"
export DEBUG="true"

log_info "Process-scoped env set:"
echo "  RUNTIME_PROVIDER = $RUNTIME_PROVIDER"
echo "  OPENCODE_SERVER_URL = $OPENCODE_SERVER_URL"
echo "  RUNTIME_ALLOW_REAL_OPENCODE_HTTP = $RUNTIME_ALLOW_REAL_OPENCODE_HTTP"
echo "  DEBUG = $DEBUG"
echo "  DATABASE_URL = (not set — using config default)"

# ── validate config ─────────────────────────────────────────────────────

log_info "Validating config..."
CONFIG_CHECK=$(cd "$PROJECT_ROOT" && python -c "
import os; os.environ['RUNTIME_PROVIDER']='opencode_http'; os.environ['OPENCODE_SERVER_URL']='$OPENCODE_URL'; os.environ['RUNTIME_ALLOW_REAL_OPENCODE_HTTP']='true'
from app.config import settings
assert str(settings.RUNTIME_PROVIDER) == 'opencode_http', f'got {settings.RUNTIME_PROVIDER}'
assert str(settings.OPENCODE_SERVER_URL) == '$OPENCODE_URL', f'got {settings.OPENCODE_SERVER_URL}'
print('CONFIG OK')
" 2>&1) || {
    exit_fail "Config validation failed: $CONFIG_CHECK"
}
log_info "Config validation: $CONFIG_CHECK"

# ── launch API ──────────────────────────────────────────────────────────

mkdir -p "$LOG_DIR" "$PID_DIR"

log_info "Launching API in opencode_http mode on 127.0.0.1:$PORT ..."

cd "$PROJECT_ROOT"
nohup python -m uvicorn --app-dir "$API_DIR" app.main:app \
    --host 127.0.0.1 --port "$PORT" \
    > "$LOG_FILE" 2>&1 &

API_PID=$!
echo "$API_PID" > "$PID_FILE"
log_info "API process started. PID: $API_PID"
log_info "Provider mode: opencode_http"
log_info "Log file: $LOG_FILE"

# ── readiness poll ──────────────────────────────────────────────────────

log_info "Verifying API endpoints (timeout ~30s)..."
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

# ── verify listener ─────────────────────────────────────────────────────

BINDS_LOCALHOST=false
BINDS_ZERO=false
BINDS_V6=false
LISTENER_PID=0

while IFS= read -r line; do
    ADDR=$(echo "$line" | awk '{print $4}' | cut -d: -f1)
    PID_VAL=$(echo "$line" | grep -oP 'pid=\K[0-9]+' || echo "0")
    if [[ "$ADDR" == "0.0.0.0" ]]; then BINDS_ZERO=true; fi
    if [[ "$ADDR" == "::" ]]; then BINDS_V6=true; fi
    if [[ "$ADDR" == "127.0.0.1" ]]; then
        BINDS_LOCALHOST=true
        LISTENER_PID="$PID_VAL"
    fi
done < <(ss -tlnp 2>/dev/null | grep ":${PORT} " || true)

# ── report ──────────────────────────────────────────────────────────────

echo ""
echo "========== Start API OpenCode Report =========="
echo "  Status        : $(if $HEALTH_OK; then echo 'STARTED'; else echo 'FAIL'; fi)"
echo "  PID           : $(if [[ $LISTENER_PID -gt 0 ]]; then echo "$LISTENER_PID"; else echo "$API_PID"; fi)"
echo "  Listen        : 127.0.0.1:$PORT"
echo "  Provider      : opencode_http"
echo "  OpenCode URL  : $OPENCODE_URL"
echo "  /health       : $(if $HEALTH_OK; then echo '200 OK'; else echo 'FAIL'; fi)"
echo "  /projects     : $(if $PROJECTS_OK; then echo '200 OK'; else echo 'FAIL'; fi)"
echo "  /agents       : $(if $AGENTS_OK; then echo '200 OK'; else echo 'FAIL'; fi)"
if $BINDS_LOCALHOST && ! $BINDS_ZERO && ! $BINDS_V6; then
    echo "  127.0.0.1 only: YES"
else
    echo "  127.0.0.1 only: WARNING"
fi
echo "  DATABASE_URL  : (not set — using config default)"
echo "  Log file      : $LOG_FILE"
echo "================================================="
echo ""

if ! $HEALTH_OK; then
    log_warn "/health did not respond within 30s."
    log_info "API process is running detached. Check logs: $LOG_FILE"
fi

exit 0
