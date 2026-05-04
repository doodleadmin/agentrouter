<#
.SYNOPSIS
    BE-11 Runtime Runbook: Bootstrap local dev database with Alembic migrations.

.DESCRIPTION
    Runs `python -m alembic upgrade head` in the apps/api directory to apply all
    pending migrations (async engine per DEV-DB-01). Skips if tables already exist
    unless -Force is specified. -Force requires explicit confirmation for local
    agent_mc DB only.

    NEVER uses DROP/TRUNCATE/DELETE. Sets DATABASE_URL process-scoped only.

.PARAMETER Force
    Re-run alembic upgrade head even if tables already exist. Requires confirmation.

.PARAMETER DryRun
    Validate preconditions only, print would-do actions, exit 0.

.EXAMPLE
    .\scripts\dev\bootstrap-db.ps1
    .\scripts\dev\bootstrap-db.ps1 -Force
    .\scripts\dev\bootstrap-db.ps1 -DryRun
#>

param(
    [switch] $Force,
    [switch] $DryRun
)

$ErrorActionPreference = "Stop"
Set-Location "F:\dev\agentrouter"

$COMPOSE_FILE = "infra\docker\docker-compose.yml"
$CONTAINER_NAME = "amc-dev-postgres"
$DB_NAME = "agent_mc"
$DB_USER = "agent_mc"
$API_DIR = "apps\api"

# ── helpers ─────────────────────────────────────────────────────────────

function Test-DbHasTables {
    # Quick check: does the alembic_version table exist?
    $checkSql = "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')"
    try {
        $result = docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -tAc $checkSql 2>&1
        if ($LASTEXITCODE -ne 0) { return $false }
        return ($result -eq "t")
    } catch {
        return $false
    }
}

function Exit-Fail {
    param([string] $Message)
    Write-Host ""
    Write-Host "========== Bootstrap DB Report =========="
    Write-Host "[FAIL] $Message"
    Write-Host "=========================================="
    Write-Host ""
    exit 1
}

# ── preconditions ───────────────────────────────────────────────────────

# 1. Docker daemon running
$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Exit-Fail "Docker daemon is not running."
}

# 2. Container running and healthy
try {
    $pgReady = docker exec $CONTAINER_NAME pg_isready -U $DB_USER -d $DB_NAME 2>&1
    if ($LASTEXITCODE -ne 0) {
        Exit-Fail "PostgreSQL container '$CONTAINER_NAME' is not healthy. Run check-db.ps1 first."
    }
} catch {
    Exit-Fail "PostgreSQL container '$CONTAINER_NAME' is not accessible. Run check-db.ps1 first."
}

# 3. Alembic installed
Push-Location $API_DIR
try {
    $alembicCheck = python -c "import alembic; print(alembic.__version__)" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        Exit-Fail "Alembic is not installed in the current Python environment: $alembicCheck"
    }
    Write-Host "[INFO] Alembic version: $($alembicCheck.Trim())"
} finally {
    Pop-Location
}

# ── guard: tables already exist? ────────────────────────────────────────

$tablesExist = Test-DbHasTables

# ── dry-run ─────────────────────────────────────────────────────────────
if ($DryRun) {
    Write-Host ""
    Write-Host "========== Bootstrap DB DryRun =========="
    Write-Host "[DRYRUN] would: set process-scoped `$env:DATABASE_URL for alembic"
    if ($tablesExist) {
        if ($Force) {
            Write-Host "[DRYRUN] would: prompt for confirmation (Force mode)"
            Write-Host "[DRYRUN] would: run 'python -m alembic upgrade head' in $API_DIR"
        } else {
            Write-Host "[DRYRUN] would: SKIP (tables exist, no -Force flag)"
        }
    } else {
        Write-Host "[DRYRUN] would: run 'python -m alembic upgrade head' in $API_DIR"
    }
    Write-Host "[DRYRUN] would: remove process-scoped DATABASE_URL after completion"
    Write-Host "[DRYRUN] would: NEVER use DROP/TRUNCATE/DELETE"
    Write-Host "=========================================="
    Write-Host ""
    exit 0
}

# ── skip if tables exist without -Force ─────────────────────────────────
if ($tablesExist -and -not $Force) {
    Write-Host ""
    Write-Host "========== Bootstrap DB Report =========="
    Write-Host "[INFO] Tables already exist (alembic_version found). Skipping bootstrap."
    Write-Host "[INFO] Use -Force to re-run migrations on local DB."
    Write-Host "=========================================="
    Write-Host ""
    exit 0
}

# ── force confirmation ──────────────────────────────────────────────────
if ($Force) {
    Write-Host ""
    Write-Host "===================================================="
    Write-Host " WARNING: -Force mode requested"
    Write-Host " This will re-run 'alembic upgrade head' on:"
    Write-Host "   DB: $DB_NAME"
    Write-Host "   User: $DB_USER"
    Write-Host "   Container: $CONTAINER_NAME"
    Write-Host ""
    Write-Host " This is ONLY safe for local dev agent_mc DB."
    Write-Host " NEVER force bootstrap production/staging databases."
    Write-Host "===================================================="
    $confirmation = Read-Host "Type 'agent_mc' to confirm"
    if ($confirmation -ne "agent_mc") {
        Exit-Fail "Confirmation failed. Expected 'agent_mc', got '$confirmation'. Aborted."
    }
    Write-Host "[INFO] Confirmation received. Proceeding with force bootstrap..."
}

# ── run alembic ─────────────────────────────────────────────────────────

# Set DATABASE_URL process-scoped ONLY (never persistent, never .env)
$originalDbUrl = $env:DATABASE_URL
$env:DATABASE_URL = "postgresql+asyncpg://agent_mc:agent_mc@localhost:5432/agent_mc"

try {
    Push-Location $API_DIR
    Write-Host "[INFO] Running alembic upgrade head in $API_DIR ..."
    $migrationOutput = python -m alembic upgrade head 2>&1
    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        Exit-Fail "Alembic upgrade failed. Output: $migrationOutput"
    }
    Pop-Location

    Write-Host "[INFO] Alembic output: $migrationOutput"

    # Verify it worked
    $verifySql = "SELECT version_num FROM alembic_version"
    $version = docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -tAc $verifySql 2>&1
    if ($LASTEXITCODE -ne 0) {
        Exit-Fail "Alembic completed but version check failed: $version"
    }

    Write-Host ""
    Write-Host "========== Bootstrap DB Report =========="
    Write-Host "[PASS] Database bootstrapped successfully"
    Write-Host "  Container : $CONTAINER_NAME"
    Write-Host "  DB        : $DB_NAME"
    Write-Host "  User      : $DB_USER"
    Write-Host "  Version   : $($version.Trim())"
    Write-Host "  Force     : $Force"
    Write-Host "=========================================="
    Write-Host ""
}
finally {
    # ALWAYS remove process-scoped DATABASE_URL
    if ($originalDbUrl) {
        $env:DATABASE_URL = $originalDbUrl
    } else {
        Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
    }
    Pop-Location -ErrorAction SilentlyContinue
}

exit 0
