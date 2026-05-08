#!/usr/bin/env bash
# rollback.sh — safe rollback orchestration (dry-run by default)

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/opt/agent-control/agentrouter}"
ENV_FILE="${ENV_FILE:-/opt/agent-control/agentrouter/.env}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
ROLLBACK_COMMIT="${ROLLBACK_COMMIT:-}"
DRY_RUN="${DRY_RUN:-true}"

CONFIRM_ROLLBACK="${CONFIRM_ROLLBACK:-no}"
CONFIRM_SERVICE_RESTART="${CONFIRM_SERVICE_RESTART:-no}"
CONFIRM_DB_ROLLBACK="${CONFIRM_DB_ROLLBACK:-no}"
ALLOW_CHECKOUT="${ALLOW_CHECKOUT:-no}"
ALLOW_INSTALL_DEPS="${ALLOW_INSTALL_DEPS:-no}"
ALLOW_DB_DOWNGRADE_EXECUTION="${ALLOW_DB_DOWNGRADE_EXECUTION:-no}"
WRITE_RELEASE_RECORD="${WRITE_RELEASE_RECORD:-no}"

DB_ROLLBACK_COMMAND="${DB_ROLLBACK_COMMAND:-python -m alembic downgrade -1}"

log_info()  { printf '[rollback][INFO] %s\n' "$*"; }
log_warn()  { printf '[rollback][WARN] %s\n' "$*"; }
log_error() { printf '[rollback][FAIL] %s\n' "$*" >&2; }
die()       { log_error "$*"; exit 1; }

check_command() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

require_confirmation() {
  local value="$1"
  local name="$2"
  if [[ "$value" != "yes" ]]; then
    die "confirmation gate not satisfied: $name=yes required"
  fi
}

dry_run_or_exec() {
  local cmd="$*"
  if [[ "$DRY_RUN" == "true" ]]; then
    log_info "DRY_RUN=true :: $cmd"
  else
    eval "$cmd"
  fi
}

write_rollback_record() {
  [[ "$WRITE_RELEASE_RECORD" == "yes" ]] || return 0

  local ts rec_dir rec_file operator
  ts="$(date +%Y%m%d-%H%M%S)"
  rec_dir="$PROJECT_ROOT/.runtime/releases"
  rec_file="$rec_dir/${ts}-rollback.txt"
  operator="$(whoami 2>/dev/null || echo unknown)"

  if [[ "$DRY_RUN" == "true" ]]; then
    log_info "DRY_RUN=true :: would write rollback record to $rec_file"
    return 0
  fi

  mkdir -p "$rec_dir"
  {
    echo "timestamp=$ts"
    echo "operator=$operator"
    echo "rollback_commit=$ROLLBACK_COMMIT"
    echo "dry_run=$DRY_RUN"
    echo "confirm_rollback=$CONFIRM_ROLLBACK"
    echo "confirm_service_restart=$CONFIRM_SERVICE_RESTART"
    echo "confirm_db_rollback=$CONFIRM_DB_ROLLBACK"
  } > "$rec_file"
  log_info "rollback record written: $rec_file"
}

[[ -n "$ROLLBACK_COMMIT" ]] || die "ROLLBACK_COMMIT is required"

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

if [[ "$DRY_RUN" != "true" ]]; then
  require_confirmation "$CONFIRM_ROLLBACK" "CONFIRM_ROLLBACK"
  require_confirmation "$CONFIRM_SERVICE_RESTART" "CONFIRM_SERVICE_RESTART"
fi

check_command git
check_command bash

log_info "PROJECT_ROOT=$PROJECT_ROOT"
log_info "ENV_FILE=$ENV_FILE"
log_info "HEALTH_URL=$HEALTH_URL"
log_info "ROLLBACK_COMMIT=$ROLLBACK_COMMIT"
log_info "DRY_RUN=$DRY_RUN"

if [[ ! -d "$PROJECT_ROOT/.git" ]]; then
  die "project root is not a git repository: $PROJECT_ROOT"
fi

dry_run_or_exec "git -C '$PROJECT_ROOT' rev-parse --verify '$ROLLBACK_COMMIT^{commit}'"

if [[ "$CONFIRM_SERVICE_RESTART" == "yes" ]]; then
  dry_run_or_exec "systemctl stop agentrouter-telegram-bot"
  dry_run_or_exec "systemctl stop agentrouter-worker"
  dry_run_or_exec "systemctl stop agentrouter-api"
else
  log_warn "CONFIRM_SERVICE_RESTART!=yes :: no service stop/start actions"
fi

if [[ "$ALLOW_CHECKOUT" == "yes" ]]; then
  dry_run_or_exec "git -C '$PROJECT_ROOT' checkout '$ROLLBACK_COMMIT'"
else
  log_info "ALLOW_CHECKOUT=no :: skipping checkout"
fi

if [[ "$ALLOW_INSTALL_DEPS" == "yes" ]]; then
  dry_run_or_exec "echo 'install dependencies for rollback (project-specific command goes here)'"
else
  log_info "ALLOW_INSTALL_DEPS=no :: skipping dependency install"
fi

if [[ "$CONFIRM_DB_ROLLBACK" == "yes" ]]; then
  if [[ "$ALLOW_DB_DOWNGRADE_EXECUTION" == "yes" ]]; then
    dry_run_or_exec "cd '$PROJECT_ROOT/apps/api' && $DB_ROLLBACK_COMMAND"
  else
    log_warn "DB rollback requested but execution disabled; printing instruction only"
    log_warn "Manual action: prefer backup restore for schema-breaking migrations"
    log_warn "Optional tested downgrade command: $DB_ROLLBACK_COMMAND"
  fi
else
  log_warn "CONFIRM_DB_ROLLBACK!=yes :: DB rollback skipped"
fi

if [[ "$CONFIRM_SERVICE_RESTART" == "yes" ]]; then
  dry_run_or_exec "systemctl start agentrouter-api"
  dry_run_or_exec "systemctl start agentrouter-worker"
  dry_run_or_exec "systemctl start agentrouter-telegram-bot"
fi

dry_run_or_exec "DRY_RUN='$DRY_RUN' HEALTH_URL='$HEALTH_URL' bash '$PROJECT_ROOT/scripts/deploy/smoke.sh'"
write_rollback_record
log_info "rollback workflow completed"
