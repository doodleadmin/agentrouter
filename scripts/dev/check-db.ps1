<#
.SYNOPSIS
    BE-11 Runtime Runbook: Database health check for local dev environment.

.DESCRIPTION
    Checks amc-dev-postgres container health, pg_isready, required tables,
    and alembic migration version. Supports -Json output and -DryRun mode.

.PARAMETER Json
    Output results as JSON instead of human-readable text.

.PARAMETER DryRun
    Validate preconditions only, print would-do actions, exit 0.

.EXAMPLE
    .\scripts\dev\check-db.ps1
    .\scripts\dev\check-db.ps1 -Json
    .\scripts\dev\check-db.ps1 -DryRun
#>

param(
    [switch] $Json,
    [switch] $DryRun
)

$ErrorActionPreference = "Stop"
Set-Location "F:\dev\agentrouter"

# ── constants ──────────────────────────────────────────────────────────
$CONTAINER_NAME = "amc-dev-postgres"
$COMPOSE_FILE = "infra\docker\docker-compose.yml"
$DB_NAME = "agent_mc"
$DB_USER = "agent_mc"
$REQUIRED_TABLES = @(
    "projects",
    "agents",
    "telegram_topics",
    "tasks",
    "task_events",
    "approvals",
    "memory_documents",
    "memory_chunks",
    "alembic_version"
)
$EXPECTED_VERSION = "0001_initial_all_tables"

# ── helpers ─────────────────────────────────────────────────────────────
function Write-Report {
    param([hashtable] $Data)
    if ($Json) {
        $Data | ConvertTo-Json -Depth 4
    }
    else {
        Write-Host ""
        Write-Host "========== DB Health Check Report =========="
        foreach ($key in $Data.Keys | Sort-Object) {
            if ($key -eq "tables") { continue }
            $val = $Data[$key]
            if ($val -is [bool]) {
                $mark = if ($val) { "[PASS]" } else { "[FAIL]" }
                Write-Host "$mark $key"
            } else {
                Write-Host "  $key : $val"
            }
        }
        if ($Data.ContainsKey("tables")) {
            Write-Host ""
            Write-Host "--- Table Status ---"
            foreach ($t in $Data.tables) {
                $mark = if ($t.exists) { "[OK]" } else { "[MISSING]" }
                Write-Host "$mark $($t.name)"
            }
        }
        Write-Host "============================================="
        Write-Host ""
    }
}

function Exit-Fail {
    param([string] $Message)
    $report = @{
        ok            = $false
        error         = $Message
        container     = $CONTAINER_NAME
        db            = $DB_NAME
        user          = $DB_USER
        timestamp     = (Get-Date -Format "o")
    }
    Write-Report $report
    exit 1
}

# ── preconditions ───────────────────────────────────────────────────────

# 1. Compose file exists
if (-not (Test-Path $COMPOSE_FILE)) {
    if ($DryRun) {
        Write-Host "[DRYRUN] would check: compose file '$COMPOSE_FILE' found"
    }
    Exit-Fail "Compose file not found: $COMPOSE_FILE"
}

# 2. Docker daemon running
$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    if ($DryRun) {
        Write-Host "[DRYRUN] would check: docker daemon running"
    }
    Exit-Fail "Docker daemon is not running or not accessible."
}

# ── dry-run output ──────────────────────────────────────────────────────
if ($DryRun) {
    Write-Host "[DRYRUN] would: check container '$CONTAINER_NAME' exists and is healthy"
    Write-Host "[DRYRUN] would: verify pg_isready for db=$DB_NAME user=$DB_USER"
    Write-Host "[DRYRUN] would: check tables: $($REQUIRED_TABLES -join ', ')"
    Write-Host "[DRYRUN] would: check alembic_version.version_num = '$EXPECTED_VERSION'"
    $report = @{
        ok        = $true
        dryrun    = $true
        container = $CONTAINER_NAME
        db        = $DB_NAME
        user      = $DB_USER
        timestamp = (Get-Date -Format "o")
    }
    Write-Report $report
    exit 0
}

# ── checks ──────────────────────────────────────────────────────────────

# 1. Container exists and is running (healthy)
$containerStatus = docker compose -f $COMPOSE_FILE ps --format json 2>&1 | ConvertFrom-Json
if (-not $containerStatus -or ($containerStatus -is [array] -and $containerStatus.Count -eq 0)) {
    Exit-Fail "No containers found via 'docker compose -f $COMPOSE_FILE ps'."
}

# Find the postgres container
$pgContainer = $containerStatus | Where-Object { $_.Name -eq $CONTAINER_NAME } | Select-Object -First 1
if (-not $pgContainer) {
    Exit-Fail "Container '$CONTAINER_NAME' not found in compose output."
}

$pgState = $pgContainer.State
$pgHealth = $pgContainer.Health
$containerRunning = ($pgState -eq "running")
$containerHealthy = ($pgHealth -eq "healthy")

if (-not $containerRunning) {
    Exit-Fail "Container '$CONTAINER_NAME' exists but state is '$pgState' (not 'running')."
}

if (-not $containerHealthy) {
    Exit-Fail "Container '$CONTAINER_NAME' is running but health is '$pgHealth' (not 'healthy')."
}

# 2. pg_isready
$pgReady = docker exec $CONTAINER_NAME pg_isready -U $DB_USER -d $DB_NAME 2>&1
if ($LASTEXITCODE -ne 0) {
    Exit-Fail "pg_isready failed: $pgReady"
}

# 3. Check all required tables exist
$tableResults = @()
foreach ($table in $REQUIRED_TABLES) {
    $checkSql = "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '$table')"
    $result = docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -tAc $checkSql 2>&1
    $exists = ($result -eq "t")
    $tableResults += @{ name = $table; exists = $exists }
    if (-not $exists) {
        $report = @{
            ok            = $false
            error         = "Missing table: '$table'"
            container     = $CONTAINER_NAME
            containerRunning = $true
            containerHealthy = $true
            pgIsReady     = $pgReady.Trim()
            db            = $DB_NAME
            user          = $DB_USER
            tables        = $tableResults
            timestamp     = (Get-Date -Format "o")
        }
        Write-Report $report
        exit 1
    }
}

# 4. Check alembic version
$versionSql = "SELECT version_num FROM alembic_version"
$alembicVersion = docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -tAc $versionSql 2>&1
$alembicVersion = $alembicVersion.Trim()
$versionMatch = ($alembicVersion -eq $EXPECTED_VERSION)

if (-not $versionMatch) {
    $report = @{
        ok                = $false
        error             = "Alembic version mismatch: expected '$EXPECTED_VERSION', got '$alembicVersion'"
        container         = $CONTAINER_NAME
        containerRunning  = $true
        containerHealthy  = $true
        pgIsReady         = $pgReady.Trim()
        db                = $DB_NAME
        user              = $DB_USER
        alembicVersion    = $alembicVersion
        expectedVersion   = $EXPECTED_VERSION
        tables            = $tableResults
        timestamp         = (Get-Date -Format "o")
    }
    Write-Report $report
    exit 1
}

# ── success ─────────────────────────────────────────────────────────────
$report = @{
    ok                = $true
    container         = $CONTAINER_NAME
    containerRunning  = $true
    containerHealthy  = $true
    pgIsReady         = $pgReady.Trim()
    db                = $DB_NAME
    user              = $DB_USER
    alembicVersion    = $alembicVersion
    expectedVersion   = $EXPECTED_VERSION
    tableCount        = $tableResults.Count
    allTablesPresent  = $true
    tables            = $tableResults
    timestamp         = (Get-Date -Format "o")
}
Write-Report $report
exit 0
