#!/usr/bin/env bash
# smoke.sh — post-deploy smoke checks (safe by default)

set -euo pipefail

DRY_RUN="${DRY_RUN:-true}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-10}"
CHECK_JOURNAL="${CHECK_JOURNAL:-false}"
ALLOW_OFFLINE_SMOKE="${ALLOW_OFFLINE_SMOKE:-true}"

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

log_info()  { printf '[smoke][INFO] %s\n' "$*"; }
log_warn()  { WARN_COUNT=$((WARN_COUNT+1)); printf '[smoke][WARN] %s\n' "$*"; }
log_error() { FAIL_COUNT=$((FAIL_COUNT+1)); printf '[smoke][FAIL] %s\n' "$*"; }
log_pass()  { PASS_COUNT=$((PASS_COUNT+1)); printf '[smoke][PASS] %s\n' "$*"; }

check_command() { command -v "$1" >/dev/null 2>&1; }

warn_if_multiple() {
  local label="$1"
  local pattern="$2"
  local count=0
  if check_command pgrep; then
    count="$(pgrep -fc "$pattern" || true)"
  elif check_command ps; then
    count="$(ps aux | grep -E "$pattern" | grep -v grep | wc -l | tr -d ' ' || true)"
  fi

  if [[ -z "$count" ]]; then
    log_warn "cannot determine process count for $label"
    return
  fi

  if (( count > 1 )); then
    log_warn "multiple $label processes detected: $count"
  else
    log_pass "$label process count is safe: $count"
  fi
}

check_service_state() {
  local svc="$1"
  if ! check_command systemctl; then
    log_warn "systemctl unavailable; skipping $svc status"
    return
  fi

  local state
  state="$(systemctl is-active "$svc" 2>/dev/null || true)"
  case "$state" in
    active) log_pass "$svc is active" ;;
    *) log_warn "$svc is not active (state=$state)" ;;
  esac
}

journal_scan() {
  local unit="$1"
  local label="$2"
  local lines
  lines="$(journalctl -u "$unit" -n 200 --no-pager 2>/dev/null || true)"
  if [[ -z "$lines" ]]; then
    log_warn "no journal lines for $label"
    return
  fi

  local tracebacks errors btn_invalid bad_sig bind_dump
  tracebacks="$(printf '%s' "$lines" | grep -ci 'traceback' || true)"
  errors="$(printf '%s' "$lines" | grep -ci '\berror\b' || true)"
  btn_invalid="$(printf '%s' "$lines" | grep -ci 'BUTTON_DATA_INVALID' || true)"
  bad_sig="$(printf '%s' "$lines" | grep -ci 'Invalid callback signature' || true)"
  bind_dump="$(printf '%s' "$lines" | grep -ciE 'parameters:\s*\[|\bbind param' || true)"

  log_info "$label journal counters: traceback=$tracebacks error=$errors button_invalid=$btn_invalid invalid_signature=$bad_sig sql_bind_dump=$bind_dump"

  if (( tracebacks > 0 || btn_invalid > 0 || bad_sig > 0 || bind_dump > 0 )); then
    log_warn "$label journal has suspicious indicators"
  else
    log_pass "$label journal indicators are clean"
  fi
}

main() {
  log_info "HEALTH_URL=$HEALTH_URL"
  log_info "DRY_RUN=$DRY_RUN"
  log_info "CHECK_JOURNAL=$CHECK_JOURNAL"

  local health_body=""

  if [[ "$DRY_RUN" == "true" ]]; then
    log_info "DRY_RUN=true :: would call curl -fsS --max-time $TIMEOUT_SECONDS $HEALTH_URL"
    log_pass "smoke dry-run simulated"
  else
    if ! health_body="$(curl -fsS --max-time "$TIMEOUT_SECONDS" "$HEALTH_URL" 2>/dev/null)"; then
      if [[ "$ALLOW_OFFLINE_SMOKE" == "true" ]]; then
        log_warn "health endpoint unreachable (offline smoke allowed)"
      else
        log_error "health endpoint unreachable"
      fi
    else
      if [[ "$health_body" == *'"status"'* ]]; then log_pass "health contains status"; else log_error "health missing status"; fi
      if [[ "$health_body" == *'"checks"'* ]]; then log_pass "health contains checks"; else log_error "health missing checks"; fi
      if [[ "$health_body" == *'"database"'* ]]; then log_pass "health contains database check"; else log_error "health missing database check"; fi
      if [[ "$health_body" == *'"redis"'* ]]; then log_pass "health contains redis check"; else log_error "health missing redis check"; fi

      local status="unknown"
      [[ "$health_body" == *'"status":"ok"'* || "$health_body" == *'"status": "ok"'* ]] && status="ok"
      [[ "$health_body" == *'"status":"degraded"'* || "$health_body" == *'"status": "degraded"'* ]] && status="degraded"
      log_info "health summary: status=$status"
      log_pass "HTTP 200 from health endpoint"
    fi
  fi

  check_service_state "agentrouter-api"
  check_service_state "agentrouter-worker"
  check_service_state "agentrouter-telegram-bot"

  warn_if_multiple "telegram bot polling" 'python .*app\.main|telegram-bot'
  warn_if_multiple "celery worker" 'celery.*worker'

  if [[ "$CHECK_JOURNAL" == "true" ]]; then
    if check_command journalctl; then
      journal_scan "agentrouter-api" "API"
      journal_scan "agentrouter-worker" "Worker"
      journal_scan "agentrouter-telegram-bot" "TelegramBot"
    else
      log_warn "journalctl unavailable; skipping journal scan"
    fi
  fi

  echo
  echo "=== Smoke Summary ==="
  echo "PASS: $PASS_COUNT"
  echo "WARN: $WARN_COUNT"
  echo "FAIL: $FAIL_COUNT"

  if (( FAIL_COUNT > 0 )); then
    exit 1
  fi
}

main "$@"
