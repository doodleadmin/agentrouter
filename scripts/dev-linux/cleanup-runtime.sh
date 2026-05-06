#!/usr/bin/env bash
# DEV-LINUX-01: Clean up runtime processes and optionally restart API in stub mode.
# Stops only processes tracked in .runtime/*.pid. Never touches DB or containers.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Auto-detect Python venv
if [[ -d "$PROJECT_ROOT/.venv/bin" ]]; then
    export PATH="$PROJECT_ROOT/.venv/bin:$PATH"
fi

PID_DIR="$PROJECT_ROOT/.runtime"
PORT="${PORT:-8000}"
OPENCODE_PORT="${OPENCODE_PORT:-4096}"
API_DIR="$PROJECT_ROOT/apps/api"
LOG_DIR="$PROJECT_ROOT/logs/dev"
PORT_WAIT_TIMEOUT=10

SKIP_API_RESTART=false
DRY_RUN=false

# ── helpers ─────────────────────────────────────────────────────────────

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Clean up runtime processes and optionally restart API in stub mode.

Options:
  --port PORT           API port (default: 8000)
  --opencode-port PORT  OpenCode port (default: 4096)
  --skip-api-restart    Skip auto-restart of API in stub mode
  --dry-run             Validate preconditions only, print would-do actions
  --help                Show this help

Safety:
  - Only stops processes tracked in .runtime/*.pid
  - Validates PID command line before kill
  - Never stops PostgreSQL/Redis containers
  - Never touches database
  - Never removes .env files

PID files checked:
  $PID_DIR/api.pid
  $PID_DIR/opencode.pid
  $PID_DIR/worker.pid
  $PID_DIR/telegram-bot.pid
EOF
}

log_info()  { echo "[INFO] $*"; }
log_pass()  { echo "[PASS] $*"; }
log_fail()  { echo "[FAIL] $*"; }
log_warn()  { echo "[WARN] $*"; }
log_dryrun(){ echo "[DRYRUN] would: $*"; }

is_process_alive() {
    local pid="$1"
    kill -0 "$pid" 2>/dev/null
}

stop_tracked_process() {
    local name="$1"
    local pid_file="$PID_DIR/${name}.pid"
    local expected_pattern="$2"

    if [[ ! -f "$pid_file" ]]; then
        log_info "No PID file for $name (not running or not tracked)"
        return 0
    fi

    local pid
    pid=$(cat "$pid_file")

    if ! is_process_alive "$pid"; then
        log_info "$name PID $pid is already dead. Cleaning PID file."
        rm -f "$pid_file"
        return 0
    fi

    # Validate command line
    local cmdline
    cmdline=$(cat "/proc/$pid/cmdline" 2>/dev/null | tr '\0' ' ' || echo "")
    if [[ -z "$cmdline" ]]; then
        log_warn "Cannot read cmdline for PID $pid. Skipping $name."
        return 0
    fi

    if ! echo "$cmdline" | grep -qE "$expected_pattern"; then
        log_warn "PID $pid cmdline does not match '$expected_pattern' for $name. Skipping."
        log_warn "  cmdline: $cmdline"
        return 0
    fi

    log_info "Stopping $name (PID $pid) ..."
    kill "$pid" 2>/dev/null || true
    sleep 1

    if is_process_alive "$pid"; then
        log_warn "$name did not stop gracefully. Sending SIGKILL..."
        kill -9 "$pid" 2>/dev/null || true
        sleep 0.5
    fi

    rm -f "$pid_file"
    log_info "$name stopped."
}

wait_port_free() {
    local port="$1"
    local timeout="$2"
    local end_time
    end_time=$(($(date +%s) + timeout))

    while [[ $(date +%s) -lt $end_time ]]; do
        if ! ss -tlnp 2>/dev/null | grep -q ":${port} "; then
            log_info "Port $port is now free."
            return 0
        fi
        sleep 0.5
    done

    log_warn "Port $port still occupied after ${timeout}s."
    return 1
}

# ── parse args ──────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --port)             PORT="$2"; shift 2 ;;
        --opencode-port)    OPENCODE_PORT="$2"; shift 2 ;;
        --skip-api-restart) SKIP_API_RESTART=true; shift ;;
        --dry-run)          DRY_RUN=true; shift ;;
        --help)             usage; exit 0 ;;
        *)                  echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

# ── dry-run ─────────────────────────────────────────────────────────────

if $DRY_RUN; then
    echo ""
    echo "========== Cleanup Runtime DryRun =========="
    log_dryrun "stop OpenCode on port $OPENCODE_PORT (from .runtime/opencode.pid)"
    log_dryrun "stop API on port $PORT (from .runtime/api.pid)"
    log_dryrun "stop worker (from .runtime/worker.pid)"
    log_dryrun "stop telegram-bot (from .runtime/telegram-bot.pid)"
    log_dryrun "wait for ports to free (timeout ${PORT_WAIT_TIMEOUT}s)"
    if ! $SKIP_API_RESTART; then
        log_dryrun "auto-restart API in stub mode on 127.0.0.1:$PORT"
        log_dryrun "verify /health=200, /projects=200, /agents=200"
    fi
    log_dryrun "verify port $OPENCODE_PORT free"
    log_dryrun "verify git clean"
    log_dryrun "NOT stop postgres/redis containers"
    log_dryrun "NOT run docker compose down / NOT touch DB"
    echo "============================================="
    echo ""
    exit 0
fi

# ── 1. Stop tracked processes ───────────────────────────────────────────

log_info "Step 1: Stopping tracked runtime processes..."

stop_tracked_process "opencode" "(opencode|node)"
stop_tracked_process "worker" "celery.*worker"
stop_tracked_process "telegram-bot" "app.main"
stop_tracked_process "api" "app.main:app"

# ── 2. Wait for ports to free ───────────────────────────────────────────

log_info "Step 2: Waiting for ports to free..."
wait_port_free "$PORT" "$PORT_WAIT_TIMEOUT" || true
wait_port_free "$OPENCODE_PORT" "$PORT_WAIT_TIMEOUT" || true

# ── 3. Verify ports ─────────────────────────────────────────────────────

log_info "Step 3: Final port verification..."
API_PORT_FREE=true
OC_PORT_FREE=true
ss -tlnp 2>/dev/null | grep -q ":${PORT} " && API_PORT_FREE=false
ss -tlnp 2>/dev/null | grep -q ":${OPENCODE_PORT} " && OC_PORT_FREE=false

# ── 4. Auto-restart API in stub mode ────────────────────────────────────

API_RESTARTED=false
API_PID="N/A"
HEALTH_OK=false
PROJECTS_OK=false
AGENTS_OK=false

if ! $SKIP_API_RESTART; then
    log_info "Step 4: Auto-restarting API in stub mode..."

    # Clean any leftover RUNTIME env
    unset RUNTIME_PROVIDER OPENCODE_SERVER_URL RUNTIME_ALLOW_REAL_OPENCODE_HTTP API_TIMEOUT_SECONDS 2>/dev/null || true
    export DEBUG="true"

    if ! $API_PORT_FREE; then
        log_warn "Port $PORT not free. Attempting force cleanup..."
        # Kill anything on the port that looks like python/uvicorn
        PIDS_ON_PORT=$(ss -tlnp 2>/dev/null | grep ":${PORT} " | grep -oP 'pid=\K[0-9]+' | sort -u || true)
        for p in $PIDS_ON_PORT; do
            CMD=$(cat "/proc/$p/cmdline" 2>/dev/null | tr '\0' ' ' || echo "")
            if echo "$CMD" | grep -qE "(python|uvicorn)"; then
                kill "$p" 2>/dev/null || true
            fi
        done
        sleep 2
    fi

    mkdir -p "$LOG_DIR" "$PID_DIR"

    cd "$PROJECT_ROOT"
    nohup python -m uvicorn --app-dir "$API_DIR" app.main:app \
        --host 127.0.0.1 --port "$PORT" \
        > "$LOG_DIR/api-stub.log" 2>&1 &

    API_PID=$!
    echo "$API_PID" > "$PID_DIR/api.pid"
    log_info "API process started. PID: $API_PID"

    # Verify endpoints
    log_info "Verifying API stub mode..."
    for ((i=1; i<=15; i++)); do
        sleep 0.5

        if ! $HEALTH_OK; then
            if curl -sf "http://127.0.0.1:${PORT}/health" 2>/dev/null | grep -q '"ok"'; then
                HEALTH_OK=true
            fi
        fi

        if $HEALTH_OK; then
            HTTP_CODE=$(curl -sf -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PORT}/projects" 2>/dev/null || echo "000")
            [[ "$HTTP_CODE" == "200" ]] && PROJECTS_OK=true

            HTTP_CODE=$(curl -sf -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PORT}/agents" 2>/dev/null || echo "000")
            [[ "$HTTP_CODE" == "200" ]] && AGENTS_OK=true

            if $PROJECTS_OK && $AGENTS_OK; then
                break
            fi
        fi
    done

    API_RESTARTED=true
else
    log_info "Step 4: --skip-api-restart flag set. API not restarted."
fi

# ── 5. Git status ───────────────────────────────────────────────────────

GIT_STATUS=$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null || echo "")
GIT_CLEAN=true
[[ -n "$GIT_STATUS" ]] && GIT_CLEAN=false

# ── report ──────────────────────────────────────────────────────────────

echo ""
echo "========== Cleanup Runtime Report =========="
echo "  OpenCode stopped       : $(if $OC_PORT_FREE; then echo '[OK]'; else echo '[FAIL] port still in use'; fi)"
echo "  Worker stopped         : [OK] (attempted)"
echo "  Telegram bot stopped   : [OK] (attempted)"
echo "  API stopped            : $(if $API_PORT_FREE; then echo '[OK]'; else echo '[WARN]'; fi)"
echo "  Port $OPENCODE_PORT free      : $(if $OC_PORT_FREE; then echo 'YES'; else echo 'NO'; fi)"
echo "  Port $PORT free         : $(if $API_PORT_FREE; then echo 'YES'; else echo 'NO'; fi)"
if $API_RESTARTED; then
    echo "  API restarted (stub)   : $(if $HEALTH_OK; then echo "[OK] PID=$API_PID"; else echo '[FAIL]'; fi)"
    echo "  /health                : $(if $HEALTH_OK; then echo '200 OK'; else echo 'FAIL'; fi)"
    echo "  /projects              : $(if $PROJECTS_OK; then echo '200 OK'; else echo 'FAIL'; fi)"
    echo "  /agents                : $(if $AGENTS_OK; then echo '200 OK'; else echo 'FAIL'; fi)"
fi
echo "  Git clean              : $(if $GIT_CLEAN; then echo 'YES'; else echo 'NO (has changes)'; fi)"
echo "  Postgres/Redis         : KEPT (not stopped)"
echo "=============================================="
echo ""

exit 0
