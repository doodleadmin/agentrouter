<#
.SYNOPSIS
    BE-11 Runtime Runbook: Start API server in opencode_http runtime mode.

.DESCRIPTION
    Requires OpenCode server healthy at the configured URL. Stops any existing
    API on the target port. Sets process-scoped RUNTIME_PROVIDER, OPENCODE_SERVER_URL,
    RUNTIME_ALLOW_REAL_OPENCODE_HTTP, DEBUG. Validates config before start.
    Starts uvicorn without reload. Verifies /health, /projects, /agents.

    NEVER sets DATABASE_URL or edits .env.

.PARAMETER Port
    Port for API (default 8000). Only binds to 127.0.0.1.

.PARAMETER OpenCodeUrl
    URL of OpenCode server (default http://127.0.0.1:4096).

.PARAMETER DryRun
    Validate preconditions only, print would-do actions, exit 0.

.EXAMPLE
    .\scripts\dev\start-api-opencode.ps1
    .\scripts\dev\start-api-opencode.ps1 -Port 8000 -OpenCodeUrl "http://127.0.0.1:4096"
    .\scripts\dev\start-api-opencode.ps1 -DryRun
#>

param(
    [int] $Port = 8000,
    [string] $OpenCodeUrl = "http://127.0.0.1:4096",
    [switch] $DryRun
)

$ErrorActionPreference = "Stop"
Set-Location "F:\dev\agentrouter"

$API_DIR = "apps\api"
$HEALTH_URL = "http://127.0.0.1:${Port}/health"
$PROJECTS_URL = "http://127.0.0.1:${Port}/projects"
$AGENTS_URL = "http://127.0.0.1:${Port}/agents"
$OPENCODE_HEALTH_URL = "${OpenCodeUrl}/global/health"
$VERIFY_RETRIES = 15
$VERIFY_DELAY_MS = 500

# ── helpers ─────────────────────────────────────────────────────────────

function Exit-Fail {
    param([string] $Message)
    Write-Host "[FAIL] $Message"
    exit 1
}

function Stop-ApiOnPort {
    param([int] $TargetPort)
    $connections = Get-NetTCPConnection -LocalPort $TargetPort -LocalAddress "127.0.0.1" -ErrorAction SilentlyContinue
    if ($connections) {
        $pids = $connections.OwningProcess | Select-Object -Unique
        foreach ($p in $pids) {
            try {
                $proc = Get-Process -Id $p -ErrorAction SilentlyContinue
                if ($proc) {
                    $procName = $proc.ProcessName
                    # Only kill uvicorn/python processes running app.main:app
                    if ($procName -match "^(python|uvicorn)$") {
                        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $p").CommandLine
                        if ($cmdLine -match "app\.main:app") {
                            Write-Host "[INFO] Stopping existing API process '$procName' (PID $p) on port $TargetPort ..."
                            Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
                            Start-Sleep -Milliseconds 1000
                        }
                    }
                }
            } catch {
                Write-Host "[WARN] Could not stop process PID $p : $_"
            }
        }
    }
}

# ── preconditions ───────────────────────────────────────────────────────

# 1. OpenCode healthy
try {
    $ocHealth = Invoke-RestMethod -Uri $OPENCODE_HEALTH_URL -TimeoutSec 5 -ErrorAction Stop
    Write-Host "[INFO] OpenCode healthy at $OpenCodeUrl"
} catch {
    Exit-Fail "OpenCode not healthy at $OpenCodeUrl. Run start-opencode.ps1 first."
}

# 2. uvicorn installed
$uvicornCheck = python -c "import uvicorn; print(uvicorn.__version__)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Exit-Fail "uvicorn is not installed."
}

# 3. DB bootstrapped
try {
    $checkSql = "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')"
    $result = docker exec amc-dev-postgres psql -U agent_mc -d agent_mc -tAc $checkSql 2>&1
    if ($LASTEXITCODE -ne 0 -or ($result.Trim() -ne "t")) {
        Exit-Fail "Database not bootstrapped. Run bootstrap-db.ps1 first."
    }
} catch {
    Exit-Fail "Database not accessible."
}

# ── dry-run ─────────────────────────────────────────────────────────────
if ($DryRun) {
    Write-Host ""
    Write-Host "========== Start API OpenCode DryRun =========="
    Write-Host "[DRYRUN] would: verify OpenCode healthy at $OpenCodeUrl"
    Write-Host "[DRYRUN] would: stop existing API on port $Port"
    Write-Host "[DRYRUN] would: set process-scoped env:"
    Write-Host "    RUNTIME_PROVIDER=opencode_http"
    Write-Host "    OPENCODE_SERVER_URL=$OpenCodeUrl"
    Write-Host "    RUNTIME_ALLOW_REAL_OPENCODE_HTTP=true"
    Write-Host "    DEBUG=true"
    Write-Host "[DRYRUN] would: validate config via python -c check"
    Write-Host "[DRYRUN] would: start uvicorn on 127.0.0.1:$Port (no reload)"
    Write-Host "[DRYRUN] would: verify /health, /projects, /agents => 200"
    Write-Host "[DRYRUN] would: NOT set DATABASE_URL"
    Write-Host "[DRYRUN] would: NOT edit .env or persistent env"
    Write-Host "================================================="
    Write-Host ""
    exit 0
}

# ── stop existing API ───────────────────────────────────────────────────
Stop-ApiOnPort -TargetPort $Port

# ── verify port free ────────────────────────────────────────────────────
Start-Sleep -Milliseconds 500
$portCheck = Get-NetTCPConnection -LocalPort $Port -LocalAddress "127.0.0.1" -ErrorAction SilentlyContinue
if ($portCheck) {
    Exit-Fail "Port $Port on 127.0.0.1 is still occupied. Cannot start API."
}

# ── set process-scoped env ──────────────────────────────────────────────

# NOTE: NEVER set DATABASE_URL — rely on config.py default
$env:RUNTIME_PROVIDER = "opencode_http"
$env:OPENCODE_SERVER_URL = $OpenCodeUrl
$env:RUNTIME_ALLOW_REAL_OPENCODE_HTTP = "true"
$env:DEBUG = "true"

Write-Host "[INFO] Process-scoped env set:"
Write-Host "  RUNTIME_PROVIDER = $env:RUNTIME_PROVIDER"
Write-Host "  OPENCODE_SERVER_URL = $env:OPENCODE_SERVER_URL"
Write-Host "  RUNTIME_ALLOW_REAL_OPENCODE_HTTP = $env:RUNTIME_ALLOW_REAL_OPENCODE_HTTP"
Write-Host "  DEBUG = $env:DEBUG"
Write-Host "  DATABASE_URL = (not set — using config default)"

# ── validate config resolves correctly ──────────────────────────────────
Write-Host "[INFO] Validating config..."
Push-Location $API_DIR
try {
    $configCheck = python -c @"
from app.config import settings
assert str(settings.RUNTIME_PROVIDER) == "opencode_http", f"RUNTIME_PROVIDER mismatch: {settings.RUNTIME_PROVIDER}"
assert str(settings.OPENCODE_SERVER_URL) == "$OpenCodeUrl", f"OPENCODE_SERVER_URL mismatch"
assert settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP is True, "RUNTIME_ALLOW_REAL_OPENCODE_HTTP must be true"
assert settings.DEBUG is True, "DEBUG must be true"
print("CONFIG OK")
"@ 2>&1

    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        Exit-Fail "Config validation failed: $configCheck"
    }
    Write-Host "[INFO] Config validation: $($configCheck.Trim())"
} finally {
    Pop-Location
}

# ── start uvicorn ───────────────────────────────────────────────────────
Write-Host "[INFO] Starting API in opencode_http mode on 127.0.0.1:$Port ..."

$apiProcess = Start-Process -FilePath "python" `
    -ArgumentList @(
        "-m", "uvicorn",
        "--app-dir", $API_DIR,
        "app.main:app",
        "--host", "127.0.0.1",
        "--port", "$Port",
        "--no-reload"
    ) `
    -PassThru `
    -NoNewWindow

$pid = $apiProcess.Id
Write-Host "[INFO] API process started. PID: $pid"
Write-Host "[INFO] Listen address: 127.0.0.1:$Port"
Write-Host "[INFO] Provider mode: opencode_http"

# ── verify endpoints ────────────────────────────────────────────────────
Write-Host "[INFO] Verifying API endpoints..."
$healthOk = $false
$projectsOk = $false
$agentsOk = $false

for ($i = 1; $i -le $VERIFY_RETRIES; $i++) {
    Start-Sleep -Milliseconds $VERIFY_DELAY_MS

    try {
        $healthResp = Invoke-RestMethod -Uri $HEALTH_URL -TimeoutSec 5 -ErrorAction Stop
        if ($healthResp.status -eq "ok") { $healthOk = $true }
    } catch { }

    if ($healthOk) {
        try { Invoke-RestMethod -Uri $PROJECTS_URL -TimeoutSec 5 -ErrorAction Stop; $projectsOk = $true } catch {
            $projectsOk = ($_.Exception.Response.StatusCode.value__ -eq 200)
        }
        try { Invoke-RestMethod -Uri $AGENTS_URL -TimeoutSec 5 -ErrorAction Stop; $agentsOk = $true } catch {
            $agentsOk = ($_.Exception.Response.StatusCode.value__ -eq 200)
        }
        if ($projectsOk -and $agentsOk) { break }
    }
}

# ── report ──────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========== Start API OpenCode Report =========="
Write-Host "  PID          : $pid"
Write-Host "  Listen       : 127.0.0.1:$Port"
Write-Host "  Provider     : opencode_http"
Write-Host "  OpenCode URL : $OpenCodeUrl"
Write-Host "  /health      : $(if ($healthOk) { '200 OK' } else { 'FAIL' })"
Write-Host "  /projects    : $(if ($projectsOk) { '200 OK' } else { 'FAIL' })"
Write-Host "  /agents      : $(if ($agentsOk) { '200 OK' } else { 'FAIL' })"
Write-Host "  DATABASE_URL : (not set — using config default)"
Write-Host "================================================="
Write-Host ""

if (-not $healthOk) { Write-Host "[WARN] /health did not respond. Check logs." }
exit 0
