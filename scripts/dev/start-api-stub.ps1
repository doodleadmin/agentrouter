<#
.SYNOPSIS
    BE-11 Runtime Runbook: Start API server in stub runtime mode.

.DESCRIPTION
    Starts the FastAPI orchestrator with RUNTIME_PROVIDER=stub (default).
    Removes any existing RUNTIME env overrides from the process.
    Sets DEBUG=true process-scoped. Does NOT set DATABASE_URL.
    Verifies /health, /projects, /agents return 200.

.PARAMETER Port
    Port to listen on (default 8000). Only binds to 127.0.0.1.

.PARAMETER NoReload
    If set, passes --no-reload to uvicorn (disable auto-reload).

.PARAMETER DryRun
    Validate preconditions only, print would-do actions, exit 0.

.EXAMPLE
    .\scripts\dev\start-api-stub.ps1
    .\scripts\dev\start-api-stub.ps1 -Port 8001
    .\scripts\dev\start-api-stub.ps1 -DryRun
#>

param(
    [int] $Port = 8000,
    [switch] $NoReload,
    [switch] $DryRun
)

$ErrorActionPreference = "Stop"
Set-Location "F:\dev\agentrouter"

$API_DIR = "apps\api"
$HEALTH_URL = "http://127.0.0.1:${Port}/health"
$PROJECTS_URL = "http://127.0.0.1:${Port}/projects"
$AGENTS_URL = "http://127.0.0.1:${Port}/agents"
$VERIFY_RETRIES = 15
$VERIFY_DELAY_MS = 500

# ── helpers ─────────────────────────────────────────────────────────────

function Exit-Fail {
    param([string] $Message)
    Write-Host "[FAIL] $Message"
    exit 1
}

function Remove-RuntimeEnvOverrides {
    Remove-Item Env:RUNTIME_PROVIDER -ErrorAction SilentlyContinue
    Remove-Item Env:OPENCODE_SERVER_URL -ErrorAction SilentlyContinue
    Remove-Item Env:RUNTIME_ALLOW_REAL_OPENCODE_HTTP -ErrorAction SilentlyContinue
    Remove-Item Env:API_TIMEOUT_SECONDS -ErrorAction SilentlyContinue
}

# ── preconditions ───────────────────────────────────────────────────────

# 1. DB bootstrapped (at least alembic_version table exists)
$COMPOSE_FILE = "infra\docker\docker-compose.yml"
if (Test-Path $COMPOSE_FILE) {
    try {
        $checkSql = "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')"
        $result = docker exec amc-dev-postgres psql -U agent_mc -d agent_mc -tAc $checkSql 2>&1
        if ($LASTEXITCODE -ne 0 -or ($result.Trim() -ne "t")) {
            Exit-Fail "Database not bootstrapped. Run bootstrap-db.ps1 first."
        }
    } catch {
        Exit-Fail "Database not accessible. Ensure postgres container is running."
    }
}

# 2. uvicorn installed
$uvicornCheck = python -c "import uvicorn; print(uvicorn.__version__)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Exit-Fail "uvicorn is not installed. Install with: pip install uvicorn"
}

# ── dry-run ─────────────────────────────────────────────────────────────
if ($DryRun) {
    Write-Host ""
    Write-Host "========== Start API Stub DryRun =========="
    Write-Host "[DRYRUN] would: remove existing RUNTIME env overrides from process"
    Write-Host "[DRYRUN] would: set process-scoped DEBUG=true"
    Write-Host "[DRYRUN] would: start uvicorn on 127.0.0.1:$Port (provider: stub, no DATABASE_URL set)"
    Write-Host "[DRYRUN] would: verify $HEALTH_URL -> 200"
    Write-Host "[DRYRUN] would: verify $PROJECTS_URL -> 200"
    Write-Host "[DRYRUN] would: verify $AGENTS_URL -> 200"
    Write-Host "============================================="
    Write-Host ""
    exit 0
}

# ── clean env ───────────────────────────────────────────────────────────

# Remove any existing RUNTIME env overrides from the process
Remove-RuntimeEnvOverrides

# Set process-scoped: DEBUG=true (no DATABASE_URL)
$env:DEBUG = "true"

# ── build uvicorn args ──────────────────────────────────────────────────
$uvicornArgs = @(
    "--app-dir", $API_DIR,
    "app.main:app",
    "--host", "127.0.0.1",
    "--port", "$Port"
)

if (-not $NoReload) {
    # With reload enabled by default for dev
} else {
    $uvicornArgs += "--no-reload"
}

# ── start uvicorn ───────────────────────────────────────────────────────
Write-Host "[INFO] Starting API in stub mode on 127.0.0.1:$Port ..."
Write-Host "[INFO] Provider mode: stub (default)"
Write-Host "[INFO] uvicorn args: $($uvicornArgs -join ' ')"

$apiProcess = Start-Process -FilePath "python" `
    -ArgumentList @("-m", "uvicorn") + $uvicornArgs `
    -PassThru `
    -NoNewWindow

$pid = $apiProcess.Id
Write-Host "[INFO] API process started. PID: $pid"
Write-Host "[INFO] Listen address: 127.0.0.1:$Port"

# ── verify endpoints ────────────────────────────────────────────────────
Write-Host "[INFO] Verifying API endpoints..."
$healthOk = $false
$projectsOk = $false
$agentsOk = $false

for ($i = 1; $i -le $VERIFY_RETRIES; $i++) {
    Start-Sleep -Milliseconds $VERIFY_DELAY_MS

    try {
        $healthResp = Invoke-RestMethod -Uri $HEALTH_URL -TimeoutSec 5 -ErrorAction Stop
        if ($healthResp.status -eq "ok") {
            $healthOk = $true
        }
    } catch {
        # still waiting
    }

    if ($healthOk) {
        try {
            $projectsResp = Invoke-RestMethod -Uri $PROJECTS_URL -TimeoutSec 5 -ErrorAction Stop
            $projectsOk = $true
        } catch {
            # Projects may return error if no DB, but 200 is expected
            $projectsOk = ($_.Exception.Response.StatusCode.value__ -eq 200)
        }

        try {
            $agentsResp = Invoke-RestMethod -Uri $AGENTS_URL -TimeoutSec 5 -ErrorAction Stop
            $agentsOk = $true
        } catch {
            $agentsOk = ($_.Exception.Response.StatusCode.value__ -eq 200)
        }

        if ($projectsOk -and $agentsOk) {
            break
        }
    }
}

# ── report ──────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========== Start API Stub Report =========="
Write-Host "  PID          : $pid"
Write-Host "  Listen       : 127.0.0.1:$Port"
Write-Host "  Provider     : stub"
Write-Host "  /health      : $(if ($healthOk) { '200 OK' } else { 'FAIL' })"
Write-Host "  /projects    : $(if ($projectsOk) { '200 OK' } else { 'FAIL' })"
Write-Host "  /agents      : $(if ($agentsOk) { '200 OK' } else { 'FAIL' })"
Write-Host "  DATABASE_URL : (not set — using config default)"
Write-Host "============================================="
Write-Host ""

if (-not $healthOk -or -not $projectsOk -or -not $agentsOk) {
    Write-Host "[WARN] Some endpoints did not return 200 within timeout."
    Write-Host "[WARN] Check if DB is properly bootstrapped and accessible."
}

exit 0
