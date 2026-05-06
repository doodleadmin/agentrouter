#!/usr/bin/env bash
# DEV-LINUX-01: Start Telegram bot gateway.
# Requires .env.local with TELEGRAM_BOT_TOKEN.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

BOT_DIR="$PROJECT_ROOT/apps/telegram-bot"
ENV_LOCAL="$PROJECT_ROOT/.env.local"
PORT="${PORT:-8000}"
API_HEALTH_URL="http://127.0.0.1:${PORT}/health"
LOG_DIR="$PROJECT_ROOT/logs/dev"
LOG_FILE="$LOG_DIR/telegram-bot.log"
PID_DIR="$PROJECT_ROOT/.runtime"
PID_FILE="$PID_DIR/telegram-bot.pid"

DRY_RUN=false

# ── helpers ─────────────────────────────────────────────────────────────

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Start Telegram bot gateway.

Options:
  --port PORT   API port for health check (default: 8000)
  --dry-run     Validate preconditions only, print would-do actions
  --help        Show this help

Requires:
  - .env.local with TELEGRAM_BOT_TOKEN set
  - API healthy at http://127.0.0.1:<port>

Working directory: $BOT_DIR
Logs: $LOG_FILE
PID:  $PID_FILE

Note: Token is NEVER displayed in output.
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
        --port)     PORT="$2"; shift 2 ;;
        --dry-run)  DRY_RUN=true; shift ;;
        --help)     usage; exit 0 ;;
        *)          echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

API_HEALTH_URL="http://127.0.0.1:${PORT}/health"

# ── preconditions ───────────────────────────────────────────────────────

# 1. .env.local exists with TELEGRAM_BOT_TOKEN
if [[ ! -f "$ENV_LOCAL" ]]; then
    exit_fail ".env.local not found at $ENV_LOCAL. Copy from .env.local.example."
fi

if ! grep -q '^TELEGRAM_BOT_TOKEN=.' "$ENV_LOCAL" 2>/dev/null; then
    exit_fail "TELEGRAM_BOT_TOKEN is not set in .env.local."
fi
log_info ".env.local found with TELEGRAM_BOT_TOKEN set."

# 2. API healthy
if ! curl -sf "$API_HEALTH_URL" >/dev/null 2>&1; then
    exit_fail "API not healthy at $API_HEALTH_URL. Start API first."
fi
log_info "API healthy at $API_HEALTH_URL"

# ── dry-run ─────────────────────────────────────────────────────────────

if $DRY_RUN; then
    echo ""
    echo "========== Start Telegram Bot DryRun =========="
    log_dryrun "source .env.local (process-scoped only)"
    log_dryrun "verify TELEGRAM_BOT_TOKEN is set (not displayed)"
    log_dryrun "start python -m app.main in $BOT_DIR"
    log_dryrun "nohup ... > $LOG_FILE 2>&1 &"
    log_dryrun "verify process alive"
    echo "================================================"
    echo ""
    exit 0
fi

# ── check if already running ────────────────────────────────────────────

if [[ -f "$PID_FILE" ]]; then
    OLD_PID=$(cat "$PID_FILE")
    if is_process_alive "$OLD_PID"; then
        CMDLINE=$(cat "/proc/$OLD_PID/cmdline" 2>/dev/null | tr '\0' ' ' || echo "")
        if echo "$CMDLINE" | grep -q "app.main"; then
            log_info "Telegram bot already running. PID: $OLD_PID"
            echo ""
            echo "========== Start Telegram Bot Report =========="
            echo "  Status : ALREADY_RUNNING"
            echo "  PID    : $OLD_PID"
            echo "  Log    : $LOG_FILE"
            echo "================================================"
            echo ""
            exit 0
        fi
    fi
    rm -f "$PID_FILE"
fi

# ── source env and start ────────────────────────────────────────────────

mkdir -p "$LOG_DIR" "$PID_DIR"

# Source .env.local into current process env (process-scoped only)
set -a
# shellcheck source=/dev/null
source "$ENV_LOCAL"
set +a

log_info "Starting Telegram bot..."
log_info "Working dir: $BOT_DIR"
log_info "Token: (set, not displayed)"

cd "$BOT_DIR"
nohup python -m app.main > "$LOG_FILE" 2>&1 &

BOT_PID=$!
echo "$BOT_PID" > "$PID_FILE"
log_info "Telegram bot started. PID: $BOT_PID"
log_info "Log file: $LOG_FILE"

# ── verify alive ────────────────────────────────────────────────────────

sleep 2
if is_process_alive "$BOT_PID"; then
    BOT_ALIVE=true
else
    BOT_ALIVE=false
fi

# ── report ──────────────────────────────────────────────────────────────

echo ""
echo "========== Start Telegram Bot Report =========="
echo "  PID    : $BOT_PID"
echo "  Alive  : $(if $BOT_ALIVE; then echo 'YES'; else echo 'NO'; fi)"
echo "  Log    : $LOG_FILE"
echo "================================================"
echo ""

if ! $BOT_ALIVE; then
    log_warn "Bot process died within 2s. Check log: $LOG_FILE"
    log_warn "Last 10 lines:"
    tail -10 "$LOG_FILE" 2>/dev/null || echo "(no log file)"
fi

exit 0
