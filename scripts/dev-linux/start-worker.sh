#!/usr/bin/env bash
# DEV-LINUX-01: Start Celery worker for background task processing.
# Requires Redis healthy and API /health=200.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Auto-detect Python venv
if [[ -d "$PROJECT_ROOT/.venv/bin" ]]; then
    export PATH="$PROJECT_ROOT/.venv/bin:$PATH"
fi

WORKER_DIR="$PROJECT_ROOT/apps/worker"
PORT="${PORT:-8000}"
API_HEALTH_URL="http://127.0.0.1:${PORT}/health"
REDIS_CONTAINER="amc-dev-redis"
QUEUES="${QUEUES:-telegram_inbound,agent_plan,agent_execute,memory_index,notifications}"
API_TIMEOUT="${API_TIMEOUT:-420}"
LOG_DIR="$PROJECT_ROOT/logs/dev"
LOG_FILE="$LOG_DIR/worker.log"
PID_DIR="$PROJECT_ROOT/.runtime"
PID_FILE="$PID_DIR/worker.pid"

DRY_RUN=false

# ── helpers ─────────────────────────────────────────────────────────────

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Start Celery worker for background task processing.

Options:
  --queues LIST       Comma-separated queue names (default: all)
  --api-timeout SEC   API timeout in seconds (default: 420)
  --port PORT         API port for health check (default: 8000)
  --dry-run           Validate preconditions only, print would-do actions
  --help              Show this help

Environment (process-scoped, never persisted):
  CELERY_BROKER_URL=redis://localhost:6379/1
  CELERY_RESULT_BACKEND=redis://localhost:6379/2
  API_BASE_URL=http://127.0.0.1:<port>
  API_TIMEOUT_SECONDS=<api-timeout>
  SANDBOX_RUNNER_MODE=fake

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

# ── parse args ──────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --queues)       QUEUES="$2"; shift 2 ;;
        --api-timeout)  API_TIMEOUT="$2"; shift 2 ;;
        --port)         PORT="$2"; shift 2 ;;
        --dry-run)      DRY_RUN=true; shift ;;
        --help)         usage; exit 0 ;;
        *)              echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

API_HEALTH_URL="http://127.0.0.1:${PORT}/health"

# ── preconditions ───────────────────────────────────────────────────────

if ! $DRY_RUN; then
    # 1. Redis healthy
    REDIS_PING=$(docker exec "$REDIS_CONTAINER" redis-cli ping 2>/dev/null || echo "FAIL")
    if [[ "$REDIS_PING" != "PONG" ]]; then
        exit_fail "Redis not healthy. Ensure '$REDIS_CONTAINER' is running and returns PONG."
    fi
    log_info "Redis healthy: PONG"

    # 2. API healthy
    if ! curl -sf "$API_HEALTH_URL" 2>/dev/null | grep -q '"ok"'; then
        exit_fail "API not healthy at $API_HEALTH_URL. Start API first."
    fi
    log_info "API healthy at $API_HEALTH_URL"

    # 3. Celery installed
    if ! python -c "import celery" 2>/dev/null; then
        exit_fail "Celery is not installed."
    fi
    CELERY_VER=$(python -c "import celery; print(celery.__version__)" 2>/dev/null || echo "unknown")
    log_info "Celery version: $CELERY_VER"
fi

# ── dry-run ─────────────────────────────────────────────────────────────

if $DRY_RUN; then
    echo ""
    echo "========== Start Worker DryRun =========="
    log_dryrun "verify Redis healthy (docker exec $REDIS_CONTAINER redis-cli ping)"
    log_dryrun "verify API /health=200 at $API_HEALTH_URL"
    log_dryrun "set process-scoped env:"
    echo "    CELERY_BROKER_URL=redis://localhost:6379/1"
    echo "    CELERY_RESULT_BACKEND=redis://localhost:6379/2"
    echo "    API_BASE_URL=http://127.0.0.1:$PORT"
    echo "    API_TIMEOUT_SECONDS=$API_TIMEOUT"
    echo "    SANDBOX_RUNNER_MODE=fake"
    log_dryrun "start celery worker (queues=$QUEUES) from $WORKER_DIR"
    log_dryrun "nohup ... > $LOG_FILE 2>&1 &"
    echo "=========================================="
    echo ""
    exit 0
fi

# ── check if already running ────────────────────────────────────────────

if [[ -f "$PID_FILE" ]]; then
    OLD_PID=$(cat "$PID_FILE")
    if is_process_alive "$OLD_PID"; then
        CMDLINE=$(cat "/proc/$OLD_PID/cmdline" 2>/dev/null | tr '\0' ' ' || echo "")
        if echo "$CMDLINE" | grep -q "celery.*worker"; then
            log_info "Worker already running. PID: $OLD_PID"
            echo ""
            echo "========== Start Worker Report =========="
            echo "  Status     : ALREADY_RUNNING"
            echo "  PID        : $OLD_PID"
            echo "  Queues     : $QUEUES"
            echo "  Broker     : redis://localhost:6379/1"
            echo "  Log file   : $LOG_FILE"
            echo "=========================================="
            echo ""
            exit 0
        fi
    fi
    rm -f "$PID_FILE"
fi

# ── set process-scoped env ──────────────────────────────────────────────

export CELERY_BROKER_URL="redis://localhost:6379/1"
export CELERY_RESULT_BACKEND="redis://localhost:6379/2"
export API_BASE_URL="http://127.0.0.1:$PORT"
export API_TIMEOUT_SECONDS="$API_TIMEOUT"
export SANDBOX_RUNNER_MODE="fake"

log_info "Process-scoped env set:"
echo "  CELERY_BROKER_URL = $CELERY_BROKER_URL"
echo "  CELERY_RESULT_BACKEND = $CELERY_RESULT_BACKEND"
echo "  API_BASE_URL = $API_BASE_URL"
echo "  API_TIMEOUT_SECONDS = $API_TIMEOUT_SECONDS"
echo "  SANDBOX_RUNNER_MODE = $SANDBOX_RUNNER_MODE"

# ── start worker ────────────────────────────────────────────────────────

mkdir -p "$LOG_DIR" "$PID_DIR"

log_info "Starting Celery worker..."
log_info "Queues: $QUEUES"
log_info "Working dir: $WORKER_DIR"

cd "$WORKER_DIR"
nohup python -m celery -A app.celery_app worker \
    --loglevel=INFO \
    --pool=solo \
    --queues="$QUEUES" \
    > "$LOG_FILE" 2>&1 &

WORKER_PID=$!
echo "$WORKER_PID" > "$PID_FILE"
log_info "Celery worker started. PID: $WORKER_PID"
log_info "Log file: $LOG_FILE"

# ── verify alive ────────────────────────────────────────────────────────

sleep 2
if is_process_alive "$WORKER_PID"; then
    WORKER_ALIVE=true
else
    WORKER_ALIVE=false
fi

# ── report ──────────────────────────────────────────────────────────────

echo ""
echo "========== Start Worker Report =========="
echo "  PID          : $WORKER_PID"
echo "  Alive        : $(if $WORKER_ALIVE; then echo 'YES'; else echo 'NO'; fi)"
echo "  Queues       : $QUEUES"
echo "  Broker       : $CELERY_BROKER_URL"
echo "  Result       : $CELERY_RESULT_BACKEND"
echo "  API Base     : $API_BASE_URL"
echo "  API Timeout  : ${API_TIMEOUT_SECONDS}s"
echo "  Sandbox Mode : $SANDBOX_RUNNER_MODE"
echo "  Working Dir  : $WORKER_DIR"
echo "  Log file     : $LOG_FILE"
echo "=========================================="
echo ""

if ! $WORKER_ALIVE; then
    log_warn "Worker process died within 2s. Check log: $LOG_FILE"
    log_warn "Last 10 lines:"
    tail -10 "$LOG_FILE" 2>/dev/null || echo "(no log file)"
fi

exit 0
