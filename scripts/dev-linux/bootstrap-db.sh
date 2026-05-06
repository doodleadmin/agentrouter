#!/usr/bin/env bash
# DEV-LINUX-01: Bootstrap local dev database with Alembic migrations.
# Runs `alembic upgrade head` in apps/api. Skips if tables already exist
# unless --force is specified. NEVER uses DROP/TRUNCATE/DELETE.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

CONTAINER_NAME="amc-dev-postgres"
DB_NAME="agent_mc"
DB_USER="agent_mc"
API_DIR="$PROJECT_ROOT/apps/api"

DRY_RUN=false
FORCE=false

# ── helpers ─────────────────────────────────────────────────────────────

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Bootstrap local dev database with Alembic migrations.

Options:
  --force       Re-run alembic upgrade head even if tables exist
  --dry-run     Validate preconditions only, print would-do actions
  --help        Show this help

Safety:
  - NEVER uses DROP/TRUNCATE/DELETE
  - Only runs 'alembic upgrade head'
  - --force requires explicit confirmation (type 'agent_mc')
  - DATABASE_URL is process-scoped only (never persisted)
EOF
}

log_info()  { echo "[INFO] $*"; }
log_pass()  { echo "[PASS] $*"; }
log_fail()  { echo "[FAIL] $*"; }
log_warn()  { echo "[WARN] $*"; }
log_dryrun(){ echo "[DRYRUN] would: $*"; }

exit_fail() {
    echo ""
    echo "========== Bootstrap DB Report =========="
    log_fail "$1"
    echo "=========================================="
    echo ""
    exit 1
}

# ── parse args ──────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --force)    FORCE=true; shift ;;
        --dry-run)  DRY_RUN=true; shift ;;
        --help)     usage; exit 0 ;;
        *)          echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

# ── preconditions ───────────────────────────────────────────────────────

# 1. Docker daemon
if ! docker info >/dev/null 2>&1; then
    exit_fail "Docker daemon is not running."
fi

# 2. Postgres container healthy
CONTAINER_STATE=$(docker inspect --format='{{.State.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "not_found")
if [[ "$CONTAINER_STATE" != "running" ]]; then
    exit_fail "PostgreSQL container '$CONTAINER_NAME' is not running (state: $CONTAINER_STATE)."
fi

if ! docker exec "$CONTAINER_NAME" pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
    exit_fail "PostgreSQL container '$CONTAINER_NAME' is not ready."
fi

# 3. Alembic installed
if ! python -c "import alembic" 2>/dev/null; then
    exit_fail "Alembic is not installed in the current Python environment."
fi

# ── check if tables exist ───────────────────────────────────────────────

TABLES_EXIST=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -tAc \
    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')" 2>/dev/null || echo "f")
TABLES_EXIST=$(echo "$TABLES_EXIST" | tr -d '[:space:]')

# ── dry-run ─────────────────────────────────────────────────────────────

if $DRY_RUN; then
    echo ""
    echo "========== Bootstrap DB DryRun =========="
    log_dryrun "set process-scoped DATABASE_URL for alembic"
    if [[ "$TABLES_EXIST" == "t" ]]; then
        if $FORCE; then
            log_dryrun "prompt for confirmation (Force mode)"
            log_dryrun "run 'python -m alembic upgrade head' in $API_DIR"
        else
            log_dryrun "SKIP (tables exist, no --force flag)"
        fi
    else
        log_dryrun "run 'python -m alembic upgrade head' in $API_DIR"
    fi
    log_dryrun "remove process-scoped DATABASE_URL after completion"
    log_dryrun "NEVER use DROP/TRUNCATE/DELETE"
    echo "=========================================="
    echo ""
    exit 0
fi

# ── skip if tables exist without --force ────────────────────────────────

if [[ "$TABLES_EXIST" == "t" ]] && ! $FORCE; then
    echo ""
    echo "========== Bootstrap DB Report =========="
    log_info "Tables already exist (alembic_version found). Skipping bootstrap."
    log_info "Use --force to re-run migrations on local DB."
    echo "=========================================="
    echo ""
    exit 0
fi

# ── force confirmation ──────────────────────────────────────────────────

if $FORCE; then
    echo ""
    echo "===================================================="
    echo " WARNING: --force mode requested"
    echo " This will re-run 'alembic upgrade head' on:"
    echo "   DB: $DB_NAME"
    echo "   User: $DB_USER"
    echo "   Container: $CONTAINER_NAME"
    echo ""
    echo " This is ONLY safe for local dev agent_mc DB."
    echo " NEVER force bootstrap production/staging databases."
    echo "===================================================="
    read -rp "Type 'agent_mc' to confirm: " CONFIRMATION
    if [[ "$CONFIRMATION" != "agent_mc" ]]; then
        exit_fail "Confirmation failed. Expected 'agent_mc', got '$CONFIRMATION'. Aborted."
    fi
    log_info "Confirmation received. Proceeding with force bootstrap..."
fi

# ── run alembic ─────────────────────────────────────────────────────────

export DATABASE_URL="postgresql+asyncpg://agent_mc:agent_mc@localhost:5432/agent_mc"

log_info "Running alembic upgrade head in $API_DIR ..."
MIGRATION_OUTPUT=$(cd "$API_DIR" && python -m alembic upgrade head 2>&1) || {
    unset DATABASE_URL
    exit_fail "Alembic upgrade failed. Output: $MIGRATION_OUTPUT"
}

log_info "Alembic output: $MIGRATION_OUTPUT"

# Verify
VERSION=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -tAc \
    "SELECT version_num FROM alembic_version" 2>/dev/null || echo "unknown")
VERSION=$(echo "$VERSION" | tr -d '[:space:]')

unset DATABASE_URL

echo ""
echo "========== Bootstrap DB Report =========="
log_pass "Database bootstrapped successfully"
echo "  Container : $CONTAINER_NAME"
echo "  DB        : $DB_NAME"
echo "  User      : $DB_USER"
echo "  Version   : $VERSION"
echo "  Force     : $FORCE"
echo "=========================================="
echo ""
exit 0
