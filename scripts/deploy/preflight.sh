#!/usr/bin/env bash
# preflight.sh — production preflight checks (dry-run safe by default)

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/opt/agent-control/agentrouter}"
ENV_FILE="${ENV_FILE:-/opt/agent-control/agentrouter/.env}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
EXPECTED_COMMIT="${EXPECTED_COMMIT:-}"
DRY_RUN="${DRY_RUN:-true}"

FAIL_COUNT=0
WARN_COUNT=0
PASS_COUNT=0

log_info()  { printf '[preflight][INFO] %s\n' "$*"; }
log_warn()  { WARN_COUNT=$((WARN_COUNT+1)); printf '[preflight][WARN] %s\n' "$*"; }
log_error() { FAIL_COUNT=$((FAIL_COUNT+1)); printf '[preflight][FAIL] %s\n' "$*"; }
log_pass()  { PASS_COUNT=$((PASS_COUNT+1)); printf '[preflight][PASS] %s\n' "$*"; }

check_command() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    log_pass "command available: $cmd"
    return 0
  fi
  log_warn "command not available: $cmd"
  return 1
}

check_file_exists() {
  local path="$1"
  if [[ -f "$path" ]]; then
    log_pass "file exists: $path"
  else
    log_error "missing file: $path"
  fi
}

check_env_status() {
  local key="$1"
  if grep -Eq "^${key}=" "$ENV_FILE"; then
    local raw
    raw="$(grep -E "^${key}=" "$ENV_FILE" | tail -n1 | cut -d'=' -f2- || true)"
    if [[ -n "${raw// /}" ]]; then
      log_pass "env key present: $key"
    else
      log_warn "env key present but empty: $key"
    fi
  else
    log_error "missing env key: $key"
  fi
}

check_env_not_true() {
  local key="$1"
  local value
  value="$(grep -E "^${key}=" "$ENV_FILE" | tail -n1 | cut -d'=' -f2- || true)"
  case "${value,,}" in
    true|1|yes|on)
      log_error "$key must not be true in production"
      ;;
    *)
      log_pass "$key is not true"
      ;;
  esac
}

check_env_permissions() {
  if ! check_command stat >/dev/null 2>&1; then
    log_warn "cannot verify env file permissions (stat unavailable)"
    return
  fi

  local perms
  perms="$(stat -c '%a' "$ENV_FILE" 2>/dev/null || true)"
  if [[ -z "$perms" ]]; then
    log_warn "unable to read permissions for $ENV_FILE"
    return
  fi

  if [[ "$perms" == "600" ]]; then
    log_pass "env file permissions are 600"
  else
    log_warn "env file permissions are $perms (recommended: 600)"
  fi
}

warn_if_multiple() {
  local label="$1"
  local pattern="$2"
  local count=0

  if check_command pgrep >/dev/null 2>&1; then
    count="$(pgrep -fc "$pattern" || true)"
  elif check_command ps >/dev/null 2>&1; then
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

check_bind_8000() {
  if check_command ss >/dev/null 2>&1; then
    if ss -tln | grep -qE '0\.0\.0\.0:8000|\[::\]:8000'; then
      log_warn "API appears exposed on 0.0.0.0:8000 or [::]:8000"
    else
      log_pass "no public bind detected on :8000"
    fi
    return
  fi

  if check_command netstat >/dev/null 2>&1; then
    if netstat -tln 2>/dev/null | grep -qE '0\.0\.0\.0:8000|:::8000'; then
      log_warn "API appears exposed on 0.0.0.0:8000 or :::8000"
    else
      log_pass "no public bind detected on :8000"
    fi
    return
  fi

  log_warn "ss/netstat not available; cannot verify :8000 bind"
}

SCRIPT_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ ! -d "$PROJECT_ROOT" ]]; then
  log_warn "PROJECT_ROOT not found: $PROJECT_ROOT; falling back to $SCRIPT_REPO_ROOT"
  PROJECT_ROOT="$SCRIPT_REPO_ROOT"
fi

if [[ "$ENV_FILE" == "/opt/agent-control/agentrouter/.env" && ! -f "$ENV_FILE" ]]; then
  if [[ -f "$PROJECT_ROOT/.env.example" ]]; then
    log_warn "ENV_FILE not found at default path; falling back to $PROJECT_ROOT/.env.example"
    ENV_FILE="$PROJECT_ROOT/.env.example"
  fi
fi

main() {
  log_info "PROJECT_ROOT=$PROJECT_ROOT"
  log_info "ENV_FILE=$ENV_FILE"
  log_info "HEALTH_URL=$HEALTH_URL"
  log_info "DRY_RUN=$DRY_RUN"

  if [[ ! -d "$PROJECT_ROOT" ]]; then
    log_error "project root not found: $PROJECT_ROOT"
  else
    log_pass "project root exists"
  fi

  if [[ ! -f "$ENV_FILE" ]]; then
    log_error "env file not found: $ENV_FILE"
  else
    if [[ "$ENV_FILE" == ".env" || "$ENV_FILE" == ".env.local" ]]; then
      log_error "refusing to run against $ENV_FILE in scripted mode"
    fi
    log_pass "env file exists (values hidden)"
    check_env_permissions
  fi

  check_file_exists "$PROJECT_ROOT/infra/deploy/Caddyfile"
  check_file_exists "$PROJECT_ROOT/infra/deploy/agentrouter-api.service"
  check_file_exists "$PROJECT_ROOT/infra/deploy/agentrouter-worker.service"
  check_file_exists "$PROJECT_ROOT/infra/deploy/agentrouter-telegram-bot.service"
  check_file_exists "$PROJECT_ROOT/scripts/deploy/validate-production-templates.sh"

  if [[ -f "$ENV_FILE" ]]; then
    check_env_status DATABASE_URL
    check_env_status REDIS_URL
    check_env_status TELEGRAM_BOT_TOKEN
    check_env_status TELEGRAM_ADMIN_USER_IDS
    check_env_status CALLBACK_SECRET
    check_env_status API_BASE_URL
    check_env_not_true DEBUG
    check_env_not_true SQL_ECHO
  fi

  if [[ -d "$PROJECT_ROOT/.git" ]]; then
    local commit
    commit="$(git -C "$PROJECT_ROOT" rev-parse HEAD 2>/dev/null || true)"
    if [[ -n "$commit" ]]; then
      log_info "current commit: $commit"
      log_pass "git commit detected"
      if [[ -n "$EXPECTED_COMMIT" && "$EXPECTED_COMMIT" != "$commit" ]]; then
        log_error "EXPECTED_COMMIT mismatch (expected $EXPECTED_COMMIT, got $commit)"
      elif [[ -n "$EXPECTED_COMMIT" ]]; then
        log_pass "EXPECTED_COMMIT matches"
      fi
    else
      log_warn "unable to detect current commit"
    fi

    if [[ -n "$(git -C "$PROJECT_ROOT" status --short 2>/dev/null || true)" ]]; then
      log_warn "working tree is not clean"
    else
      log_pass "working tree clean"
    fi
  else
    log_warn "no .git directory at PROJECT_ROOT"
  fi

  check_command systemctl || true
  check_command caddy || true
  check_command docker || true

  if command -v docker >/dev/null 2>&1; then
    if docker compose version >/dev/null 2>&1; then
      log_pass "docker compose available"
    else
      log_warn "docker compose unavailable"
    fi
  fi

  warn_if_multiple "uvicorn" 'uvicorn|app\.main:app'
  warn_if_multiple "celery worker" 'celery.*worker'
  warn_if_multiple "telegram bot polling" 'python .*app\.main|telegram-bot'
  check_bind_8000

  if [[ -f "$PROJECT_ROOT/scripts/deploy/validate-production-templates.sh" ]]; then
    if [[ "$DRY_RUN" == "true" ]]; then
      log_info "DRY_RUN=true :: would run template validation script"
    else
      if bash "$PROJECT_ROOT/scripts/deploy/validate-production-templates.sh"; then
        log_pass "template validation passed"
      else
        log_error "template validation failed"
      fi
    fi
  fi

  echo
  echo "=== Preflight Summary ==="
  echo "PASS: $PASS_COUNT"
  echo "WARN: $WARN_COUNT"
  echo "FAIL: $FAIL_COUNT"

  if (( FAIL_COUNT > 0 )); then
    exit 1
  fi
}

main "$@"
