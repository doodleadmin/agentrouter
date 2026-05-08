#!/usr/bin/env bash
# release.sh — safe release orchestration (dry-run by default)

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/opt/agent-control/agentrouter}"
ENV_FILE="${ENV_FILE:-/opt/agent-control/agentrouter/.env}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
RELEASE_COMMIT="${RELEASE_COMMIT:-}"
DRY_RUN="${DRY_RUN:-true}"

CONFIRM_PRODUCTION_DEPLOY="${CONFIRM_PRODUCTION_DEPLOY:-no}"
CONFIRM_SERVICE_RESTART="${CONFIRM_SERVICE_RESTART:-no}"
CONFIRM_MIGRATIONS="${CONFIRM_MIGRATIONS:-no}"
ALLOW_GIT_FETCH="${ALLOW_GIT_FETCH:-no}"
ALLOW_GIT_PULL="${ALLOW_GIT_PULL:-no}"
ALLOW_CODE_UPDATE="${ALLOW_CODE_UPDATE:-no}"
ALLOW_INSTALL_DEPS="${ALLOW_INSTALL_DEPS:-no}"
WRITE_RELEASE_RECORD="${WRITE_RELEASE_RECORD:-no}"

MIGRATION_COMMAND="${MIGRATION_COMMAND:-python -m alembic upgrade head}"

log_info()  { printf '[release][INFO] %s\n' "$*"; }
log_warn()  { printf '[release][WARN] %s\n' "$*"; }
log_error() { printf '[release][FAIL] %s\n' "$*" >&2; }
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

write_release_record() {
  [[ "$WRITE_RELEASE_RECORD" == "yes" ]] || return 0

  local ts rec_dir rec_file operator
  ts="$(date +%Y%m%d-%H%M%S)"
  rec_dir="$PROJECT_ROOT/.runtime/releases"
  rec_file="$rec_dir/${ts}-release.txt"
  operator="$(whoami 2>/dev/null || echo unknown)"

  if [[ "$DRY_RUN" == "true" ]]; then
    log_info "DRY_RUN=true :: would write release record to $rec_file"
    return 0
  fi

  mkdir -p "$rec_dir"
  {
    echo "timestamp=$ts"
    echo "operator=$operator"
    echo "commit=$RELEASE_COMMIT"
    echo "dry_run=$DRY_RUN"
    echo "confirm_production_deploy=$CONFIRM_PRODUCTION_DEPLOY"
    echo "confirm_service_restart=$CONFIRM_SERVICE_RESTART"
    echo "confirm_migrations=$CONFIRM_MIGRATIONS"
  } > "$rec_file"
  log_info "release record written: $rec_file"
}

[[ -n "$RELEASE_COMMIT" ]] || die "RELEASE_COMMIT is required"

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
  require_confirmation "$CONFIRM_PRODUCTION_DEPLOY" "CONFIRM_PRODUCTION_DEPLOY"
  require_confirmation "$CONFIRM_SERVICE_RESTART" "CONFIRM_SERVICE_RESTART"
fi

check_command git
check_command bash

log_info "PROJECT_ROOT=$PROJECT_ROOT"
log_info "ENV_FILE=$ENV_FILE"
log_info "HEALTH_URL=$HEALTH_URL"
log_info "RELEASE_COMMIT=$RELEASE_COMMIT"
log_info "DRY_RUN=$DRY_RUN"

if [[ ! -d "$PROJECT_ROOT" ]]; then
  die "project root does not exist: $PROJECT_ROOT"
fi

if [[ ! -d "$PROJECT_ROOT/.git" ]]; then
  die "project root is not a git repository: $PROJECT_ROOT"
fi

if [[ "$ALLOW_GIT_FETCH" == "yes" ]]; then
  dry_run_or_exec "git -C '$PROJECT_ROOT' fetch --all --tags"
else
  log_info "ALLOW_GIT_FETCH=no :: skipping git fetch"
fi

if [[ "$ALLOW_GIT_PULL" == "yes" ]]; then
  dry_run_or_exec "git -C '$PROJECT_ROOT' pull"
else
  log_info "ALLOW_GIT_PULL=no :: skipping git pull"
fi

dry_run_or_exec "git -C '$PROJECT_ROOT' rev-parse --verify '$RELEASE_COMMIT^{commit}'"

dry_run_or_exec "DRY_RUN='$DRY_RUN' EXPECTED_COMMIT='$RELEASE_COMMIT' PROJECT_ROOT='$PROJECT_ROOT' ENV_FILE='$ENV_FILE' HEALTH_URL='$HEALTH_URL' bash '$PROJECT_ROOT/scripts/deploy/preflight.sh'"

if [[ "$ALLOW_CODE_UPDATE" == "yes" ]]; then
  dry_run_or_exec "git -C '$PROJECT_ROOT' checkout '$RELEASE_COMMIT'"
else
  log_info "ALLOW_CODE_UPDATE=no :: skipping code update/checkout"
fi

if [[ "$ALLOW_INSTALL_DEPS" == "yes" ]]; then
  dry_run_or_exec "echo 'install dependencies (project-specific command goes here)'"
else
  log_info "ALLOW_INSTALL_DEPS=no :: skipping dependency install"
fi

if [[ "$CONFIRM_MIGRATIONS" == "yes" ]]; then
  dry_run_or_exec "cd '$PROJECT_ROOT/apps/api' && $MIGRATION_COMMAND"
else
  log_warn "CONFIRM_MIGRATIONS!=yes :: migrations skipped"
fi

if [[ "$CONFIRM_SERVICE_RESTART" == "yes" ]]; then
  dry_run_or_exec "systemctl stop agentrouter-telegram-bot"
  dry_run_or_exec "systemctl stop agentrouter-worker"
  dry_run_or_exec "systemctl restart agentrouter-api"
  dry_run_or_exec "systemctl start agentrouter-worker"
  dry_run_or_exec "systemctl start agentrouter-telegram-bot"
else
  log_warn "CONFIRM_SERVICE_RESTART!=yes :: no service restart actions"
fi

dry_run_or_exec "DRY_RUN='$DRY_RUN' HEALTH_URL='$HEALTH_URL' bash '$PROJECT_ROOT/scripts/deploy/smoke.sh'"

write_release_record

log_info "release workflow completed"
