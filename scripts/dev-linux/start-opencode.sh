#!/usr/bin/env bash
# DEV-LINUX-01: Start OpenCode server for real runtime provider.
# Launches opencode serve on 127.0.0.1:4096.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PORT="${PORT:-4096}"
HEALTH_URL="http://127.0.0.1:${PORT}/global/health"
DOC_URL="http://127.0.0.1:${PORT}/doc"
LOG_DIR="$PROJECT_ROOT/logs/dev"
LOG_FILE="$LOG_DIR/opencode.log"
PID_DIR="$PROJECT_ROOT/.runtime"
PID_FILE="$PID_DIR/opencode.pid"
VERIFY_RETRIES=30
VERIFY_DELAY=1

DRY_RUN=false

# ── helpers ─────────────────────────────────────────────────────────────

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Start OpenCode server on 127.0.0.1:${PORT}.

Options:
  --port PORT   Port for OpenCode server (default: 4096)
  --dry-run     Validate preconditions only, print would-do actions
  --help        Show this help

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

kill_stale_on_port() {
    local port="$1"
    local pids
    pids=$(ss -tlnp 2>/dev/null | grep ":${port} " | grep -oP 'pid=\K[0-9]+' | sort -u || true)
    for pid in $pids; do
        local cmd
        cmd=$(cat "/proc/$pid/cmdline" 2>/dev/null | tr '\0' ' ' || echo "")
        if echo "$cmd" | grep -qE '(opencode|node)'; then
            log_info "Killing stale process (PID $pid) on port $port"
            kill "$pid" 2>/dev/null || true
            sleep 0.5
        else
            log_warn "Port $port occupied by PID $pid (not opencode/node), skipping"
        fi
    done
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

HEALTH_URL="http://127.0.0.1:${PORT}/global/health"
DOC_URL="http://127.0.0.1:${PORT}/doc"

# ── preconditions ───────────────────────────────────────────────────────

# Check opencode CLI
if ! command -v opencode >/dev/null 2>&1; then
    # Try npx fallback
    if command -v npx >/dev/null 2>&1; then
        log_info "opencode CLI not in PATH, will use 'npx opencode'"
    else
        exit_fail "OpenCode launcher not found. Install with: npm install -g opencode"
    fi
fi

# ── fast-path: already running ──────────────────────────────────────────

if ! $DRY_RUN; then
    if curl -sf "$HEALTH_URL" 2>/dev/null | grep -q '"healthy"'; then
        LISTENER_PID=$(ss -tlnp 2>/dev/null | grep ":${PORT} " | grep -oP 'pid=\K[0-9]+' | head -1 || echo "0")
        echo ""
        echo "========== Start OpenCode Report =========="
        echo "  Status         : ALREADY_RUNNING"
        echo "  Listen         : 127.0.0.1:$PORT"
        [[ "$LISTENER_PID" != "0" ]] && echo "  ListenerPID    : $LISTENER_PID"
        echo "  /global/health : 200 OK"
        if curl -sf "$DOC_URL" >/dev/null 2>&1; then
            echo "  /doc           : 200 OK"
        else
            echo "  /doc           : NOT ready (health OK was enough)"
        fi
        echo "============================================="
        echo ""
        exit 0
    fi
fi

# ── dry-run ─────────────────────────────────────────────────────────────

if $DRY_RUN; then
    echo ""
    echo "========== Start OpenCode DryRun =========="
    log_dryrun "resolve opencode launcher"
    log_dryrun "kill stale opencode/node processes on port $PORT"
    log_dryrun "verify port $PORT free on 127.0.0.1"
    log_dryrun "launch opencode serve on 127.0.0.1:$PORT"
    log_dryrun "poll $HEALTH_URL up to ${VERIFY_RETRIES}s"
    log_dryrun "poll $DOC_URL up to ${VERIFY_RETRIES}s"
    log_dryrun "verify listener only on 127.0.0.1"
    echo "============================================="
    echo ""
    exit 0
fi

# ── kill stale ──────────────────────────────────────────────────────────

kill_stale_on_port "$PORT"
sleep 0.5

# ── verify port free ────────────────────────────────────────────────────

if ss -tlnp 2>/dev/null | grep -q ":${PORT} "; then
    exit_fail "Port $PORT on 127.0.0.1 still occupied after cleanup."
fi

# ── launch OpenCode ─────────────────────────────────────────────────────

mkdir -p "$LOG_DIR" "$PID_DIR"

log_info "Launching OpenCode on 127.0.0.1:$PORT ..."

if command -v opencode >/dev/null 2>&1; then
    nohup opencode serve --port "$PORT" --hostname 127.0.0.1 \
        > "$LOG_FILE" 2>&1 &
else
    nohup npx opencode serve --port "$PORT" --hostname 127.0.0.1 \
        > "$LOG_FILE" 2>&1 &
fi

OC_PID=$!
echo "$OC_PID" > "$PID_FILE"
log_info "OpenCode process started. PID: $OC_PID"
log_info "Log file: $LOG_FILE"

# ── readiness poll ──────────────────────────────────────────────────────

log_info "Verifying OpenCode endpoints..."
HEALTH_OK=false
DOC_OK=false

for ((i=1; i<=VERIFY_RETRIES; i++)); do
    sleep "$VERIFY_DELAY"

    if ! $HEALTH_OK; then
        if curl -sf "$HEALTH_URL" 2>/dev/null | grep -q '"healthy"'; then
            HEALTH_OK=true
        fi
    fi

    if $HEALTH_OK && ! $DOC_OK; then
        if curl -sf "$DOC_URL" >/dev/null 2>&1; then
            DOC_OK=true
        fi
    fi

    if $HEALTH_OK && $DOC_OK; then
        break
    fi
done

# ── verify listener ─────────────────────────────────────────────────────

BINDS_LOCALHOST=false
BINDS_ZERO=false
LISTENER_PID=0

while IFS= read -r line; do
    ADDR=$(echo "$line" | awk '{print $4}' | cut -d: -f1)
    PID_VAL=$(echo "$line" | grep -oP 'pid=\K[0-9]+' || echo "0")
    if [[ "$ADDR" == "127.0.0.1" || "$ADDR" == "0.0.0.0" ]]; then
        if [[ "$ADDR" == "0.0.0.0" ]]; then
            BINDS_ZERO=true
        fi
        if [[ "$ADDR" == "127.0.0.1" ]]; then
            BINDS_LOCALHOST=true
            LISTENER_PID="$PID_VAL"
        fi
    fi
done < <(ss -tlnp 2>/dev/null | grep ":${PORT} " || true)

# ── report ──────────────────────────────────────────────────────────────

echo ""
echo "========== Start OpenCode Report =========="
echo "  Listen         : 127.0.0.1:$PORT"
[[ "$LISTENER_PID" != "0" ]] && echo "  ListenerPID    : $LISTENER_PID"
echo "  /global/health : $(if $HEALTH_OK; then echo '200 OK'; else echo 'FAIL'; fi)"
echo "  /doc           : $(if $DOC_OK; then echo '200 OK'; else echo 'FAIL'; fi)"
if $BINDS_LOCALHOST && ! $BINDS_ZERO; then
    echo "  127.0.0.1 only : YES"
else
    echo "  127.0.0.1 only : WARNING"
fi
echo "  Log file       : $LOG_FILE"
echo "============================================="
echo ""

if ! $HEALTH_OK; then
    exit_fail "OpenCode readiness failed within ${VERIFY_RETRIES}s. /global/health not healthy."
fi

if $BINDS_ZERO || ! $BINDS_LOCALHOST; then
    exit_fail "Listener validation failed: expected 127.0.0.1 only."
fi

exit 0
