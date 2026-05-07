#!/usr/bin/env bash
# INFRA-01: Seed dev database with required bootstrap records.
# Ensures agentrouter project and studio-orchestrator agent exist
# with platform-correct repo_path. Idempotent — safe to run multiple times.
# NEVER uses DROP/TRUNCATE/DELETE.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Auto-detect Python venv
if [[ -d "$PROJECT_ROOT/.venv/bin" ]]; then
    export PATH="$PROJECT_ROOT/.venv/bin:$PATH"
fi

CONTAINER_NAME="amc-dev-postgres"
DB_NAME="agent_mc"
DB_USER="agent_mc"
PROJECT_SLUG="agentrouter"
AGENT_SLUG="studio-orchestrator"
REPO_PATH="$(realpath "$PROJECT_ROOT")"

DRY_RUN=false

# ── helpers ─────────────────────────────────────────────────────────────

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Seed local dev database with required bootstrap records.
Ensures agentrouter project and studio-orchestrator agent exist.

Options:
  --dry-run     Validate preconditions only, print would-do actions
  --help        Show this help

Safety:
  - NEVER uses DROP/TRUNCATE/DELETE
  - Uses INSERT ... ON CONFLICT DO UPDATE for idempotency
  - repo_path uses realpath of PROJECT_ROOT (platform-correct)
  - No secrets are printed
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

# ── detect psql runner ──────────────────────────────────────────────────

_psql() {
    # Try native psql first, fall back to Docker exec
    if command -v psql >/dev/null 2>&1; then
        PGPASSWORD=agent_mc psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -tAc "$1" 2>/dev/null
    elif docker info >/dev/null 2>&1; then
        docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -tAc "$1" 2>/dev/null
    else
        echo ""
    fi
}

_psql_cmd() {
    # Run SQL and return raw output (no trimming)
    if command -v psql >/dev/null 2>&1; then
        PGPASSWORD=agent_mc psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -c "$1" 2>&1
    elif docker info >/dev/null 2>&1; then
        docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "$1" 2>/dev/null
    else
        echo "ERROR: no psql or docker available"
    fi
}

# ── parse args ──────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)  DRY_RUN=true; shift ;;
        --help)     usage; exit 0 ;;
        *)          echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

# ── preconditions ───────────────────────────────────────────────────────

if ! $DRY_RUN; then
    # DB must be accessible
    READY=$(_psql "SELECT 1" 2>/dev/null)
    READY=$(echo "$READY" | tr -d '[:space:]')
    if [[ "$READY" != "1" ]]; then
        exit_fail "Database not accessible. Run bootstrap-db.sh first and ensure PostgreSQL is running."
    fi
    log_info "Database accessible: db=$DB_NAME user=$DB_USER"
    log_info "Project root: $REPO_PATH"
fi

# ── seed project ────────────────────────────────────────────────────────

PROJECT_EXISTS=$(_psql "SELECT EXISTS (SELECT 1 FROM projects WHERE slug = '$PROJECT_SLUG')")
PROJECT_EXISTS=$(echo "$PROJECT_EXISTS" | tr -d '[:space:]')

PROJECT_UUID=$(python3 -c "import uuid; print(uuid.uuid4())" 2>/dev/null || echo "")

if $DRY_RUN; then
    echo ""
    echo "========== Bootstrap Seed DryRun =========="
    log_dryrun "verify database accessible"
    if [[ "$PROJECT_EXISTS" == "t" ]]; then
        log_dryrun "project '$PROJECT_SLUG' exists — update repo_path to '$REPO_PATH' if needed"
    else
        log_dryrun "create project '$PROJECT_SLUG' with repo_path='$REPO_PATH'"
    fi
    log_dryrun "ensure agent '$AGENT_SLUG' exists"
    log_dryrun "NEVER uses DROP/TRUNCATE/DELETE"
    echo "=========================================="
    echo ""
    exit 0
fi

if [[ "$PROJECT_EXISTS" == "t" ]]; then
    CURRENT_PATH=$(_psql "SELECT repo_path FROM projects WHERE slug = '$PROJECT_SLUG'")
    CURRENT_PATH=$(echo "$CURRENT_PATH" | tr -d '[:space:]')
    if [[ "$CURRENT_PATH" != "$REPO_PATH" ]]; then
        log_warn "Project '$PROJECT_SLUG' repo_path mismatch:"
        log_warn "  current : $CURRENT_PATH"
        log_warn "  expected: $REPO_PATH"
        _psql "UPDATE projects SET repo_path = '$REPO_PATH', updated_at = NOW() WHERE slug = '$PROJECT_SLUG'" >/dev/null 2>&1
        log_pass "Project '$PROJECT_SLUG' repo_path updated to: $REPO_PATH"
    else
        log_info "Project '$PROJECT_SLUG' repo_path is correct: $REPO_PATH"
    fi
else
    log_info "Creating project '$PROJECT_SLUG' ..."
    _psql "INSERT INTO projects (id, slug, name, repo_path, memory_path, default_branch, status, stack, created_at, updated_at)
           VALUES ('$PROJECT_UUID', '$PROJECT_SLUG', 'Agent Mission Control',
                   '$REPO_PATH', '.ai_memory', 'main', 'active', '{}'::jsonb, NOW(), NOW())" >/dev/null 2>&1 || exit_fail "Failed to create project."
    log_pass "Project '$PROJECT_SLUG' created with repo_path: $REPO_PATH"
fi

# ── seed agent ──────────────────────────────────────────────────────────

AGENT_EXISTS=$(_psql "SELECT EXISTS (SELECT 1 FROM agents WHERE slug = '$AGENT_SLUG')")
AGENT_EXISTS=$(echo "$AGENT_EXISTS" | tr -d '[:space:]')

AGENT_UUID=$(python3 -c "import uuid; print(uuid.uuid4())" 2>/dev/null || echo "")

if [[ "$AGENT_EXISTS" != "t" ]]; then
    log_info "Creating agent '$AGENT_SLUG' ..."
    _psql "INSERT INTO agents (id, slug, name, role, system_prompt, model, permissions, status, created_at, updated_at)
           VALUES ('$AGENT_UUID', '$AGENT_SLUG', 'Studio Orchestrator',
                   'orchestrator',
                   'You are Studio Orchestrator for Agent Mission Control. You coordinate tasks, route to specialists, and control MVP scope.',
                   'stub', '{}'::jsonb, 'active', NOW(), NOW())" >/dev/null 2>&1 || exit_fail "Failed to create agent."
    log_pass "Agent '$AGENT_SLUG' created."
else
    log_info "Agent '$AGENT_SLUG' already exists."
fi

# ── report ──────────────────────────────────────────────────────────────

echo ""
echo "========== Bootstrap Seed Report =========="
echo "  Project slug   : $PROJECT_SLUG"
echo "  Repo path      : $REPO_PATH"
echo "  Agent slug     : $AGENT_SLUG"
echo "  DB             : $DB_NAME"
log_pass "Seed complete."
echo "=========================================="
echo ""
exit 0
