#!/usr/bin/env bash
# DEV-LINUX-01: Database health check for local dev environment.
# Checks amc-dev-postgres container health, pg_isready, required tables,
# and alembic migration version.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

CONTAINER_NAME="amc-dev-postgres"
COMPOSE_FILE="$PROJECT_ROOT/infra/docker/docker-compose.yml"
DB_NAME="agent_mc"
DB_USER="agent_mc"
EXPECTED_VERSION="0001_initial_all_tables"

REQUIRED_TABLES=(
    "projects"
    "agents"
    "telegram_topics"
    "tasks"
    "task_events"
    "approvals"
    "memory_documents"
    "memory_chunks"
    "alembic_version"
)

JSON_MODE=false
DRY_RUN=false

# ── helpers ─────────────────────────────────────────────────────────────

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Database health check for local dev environment.

Options:
  --json        Output results as JSON
  --dry-run     Validate preconditions only, print would-do actions
  --help        Show this help

Checks:
  1. Docker daemon running
  2. amc-dev-postgres container running + healthy
  3. pg_isready for agent_mc database
  4. All 9 required tables exist
  5. alembic_version matches expected
EOF
}

log_info()  { echo "[INFO] $*"; }
log_pass()  { echo "[PASS] $*"; }
log_fail()  { echo "[FAIL] $*"; }
log_dryrun(){ echo "[DRYRUN] would: $*"; }

exit_fail() {
    local msg="$1"
    if $JSON_MODE; then
        cat <<EOJSON
{"ok":false,"error":"$msg","container":"$CONTAINER_NAME","db":"$DB_NAME","user":"$DB_USER","timestamp":"$(date -Iseconds)"}
EOJSON
    else
        echo ""
        echo "========== DB Health Check Report =========="
        log_fail "$msg"
        echo "============================================="
        echo ""
    fi
    exit 1
}

# ── parse args ──────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)    JSON_MODE=true; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        --help)    usage; exit 0 ;;
        *)         echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

# ── preconditions ───────────────────────────────────────────────────────

if [[ ! -f "$COMPOSE_FILE" ]]; then
    exit_fail "Compose file not found: $COMPOSE_FILE"
fi

if ! docker info >/dev/null 2>&1; then
    if $DRY_RUN; then log_dryrun "check docker daemon running"; fi
    exit_fail "Docker daemon is not running or not accessible."
fi

# ── dry-run ─────────────────────────────────────────────────────────────

if $DRY_RUN; then
    echo ""
    echo "========== DB Health Check DryRun =========="
    log_dryrun "check container '$CONTAINER_NAME' exists and is healthy"
    log_dryrun "verify pg_isready for db=$DB_NAME user=$DB_USER"
    log_dryrun "check tables: ${REQUIRED_TABLES[*]}"
    log_dryrun "check alembic_version.version_num = '$EXPECTED_VERSION'"
    echo "============================================="
    echo ""
    exit 0
fi

# ── 1. container running + healthy ──────────────────────────────────────

CONTAINER_STATE=$(docker inspect --format='{{.State.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "not_found")
if [[ "$CONTAINER_STATE" != "running" ]]; then
    exit_fail "Container '$CONTAINER_NAME' state is '$CONTAINER_STATE' (expected 'running')."
fi

CONTAINER_HEALTH=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$CONTAINER_NAME" 2>/dev/null || echo "unknown")
if [[ "$CONTAINER_HEALTH" != "healthy" && "$CONTAINER_HEALTH" != "no-healthcheck" ]]; then
    exit_fail "Container '$CONTAINER_NAME' health is '$CONTAINER_HEALTH' (expected 'healthy')."
fi

# ── 2. pg_isready ───────────────────────────────────────────────────────

if ! docker exec "$CONTAINER_NAME" pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
    exit_fail "pg_isready failed for db=$DB_NAME user=$DB_USER."
fi

# ── 3. check tables ─────────────────────────────────────────────────────

TABLE_RESULTS=()
ALL_TABLES_PRESENT=true

for TABLE in "${REQUIRED_TABLES[@]}"; do
    EXISTS=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -tAc \
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '$TABLE')" 2>/dev/null || echo "f")
    EXISTS=$(echo "$EXISTS" | tr -d '[:space:]')
    if [[ "$EXISTS" == "t" ]]; then
        TABLE_RESULTS+=("{\"name\":\"$TABLE\",\"exists\":true}")
    else
        TABLE_RESULTS+=("{\"name\":\"$TABLE\",\"exists\":false}")
        ALL_TABLES_PRESENT=false
    fi
done

if ! $ALL_TABLES_PRESENT; then
    exit_fail "One or more required tables are missing."
fi

# ── 4. alembic version ──────────────────────────────────────────────────

ALEMBIC_VERSION=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -tAc \
    "SELECT version_num FROM alembic_version" 2>/dev/null || echo "")
ALEMBIC_VERSION=$(echo "$ALEMBIC_VERSION" | tr -d '[:space:]')
VERSION_MATCH=false
[[ "$ALEMBIC_VERSION" == "$EXPECTED_VERSION" ]] && VERSION_MATCH=true

# ── report ──────────────────────────────────────────────────────────────

if $JSON_MODE; then
    TABLES_JSON=$(IFS=,; echo "${TABLE_RESULTS[*]}")
    cat <<EOJSON
{
  "ok": $VERSION_MATCH,
  "container": "$CONTAINER_NAME",
  "containerRunning": true,
  "containerHealthy": true,
  "pgIsReady": true,
  "db": "$DB_NAME",
  "user": "$DB_USER",
  "alembicVersion": "$ALEMBIC_VERSION",
  "expectedVersion": "$EXPECTED_VERSION",
  "versionMatch": $VERSION_MATCH,
  "tableCount": ${#REQUIRED_TABLES[@]},
  "allTablesPresent": $ALL_TABLES_PRESENT,
  "tables": [$TABLES_JSON],
  "timestamp": "$(date -Iseconds)"
}
EOJSON
else
    echo ""
    echo "========== DB Health Check Report =========="
    log_pass "container: $CONTAINER_NAME (running, healthy)"
    log_pass "pg_isready: db=$DB_NAME user=$DB_USER"
    echo "  alembicVersion : $ALEMBIC_VERSION"
    echo "  expectedVersion: $EXPECTED_VERSION"
    if $VERSION_MATCH; then
        log_pass "alembic version matches"
    else
        log_fail "alembic version mismatch"
    fi
    echo ""
    echo "--- Table Status ---"
    for TABLE in "${REQUIRED_TABLES[@]}"; do
        echo "[OK] $TABLE"
    done
    echo "  tableCount     : ${#REQUIRED_TABLES[@]}"
    echo "============================================="
    echo ""
fi

if ! $VERSION_MATCH; then
    exit 1
fi
exit 0
