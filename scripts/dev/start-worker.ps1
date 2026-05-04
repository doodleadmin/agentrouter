<#
.SYNOPSIS
    BE-11 Runtime Runbook: Start Celery worker for background task processing.

.DESCRIPTION
    Requires Redis healthy and API /health=200. Sets process-scoped env vars
    for Celery broker, result backend, and API timeout. Starts celery worker
    consuming from specified queues. Does NOT edit .env or persistent env.

.PARAMETER Concurrency
    Number of worker processes (default 4).

.PARAMETER Queues
    Comma-separated queue names (default: telegram_inbound,agent_plan,agent_execute,memory_index,notifications).

.PARAMETER ApiTimeout
    API timeout in seconds for worker -> API calls (default 420).

.PARAMETER DryRun
    Validate preconditions only, print would-do actions, exit 0.

.EXAMPLE
    .\scripts\dev\start-worker.ps1
    .\scripts\dev\start-worker.ps1 -Concurrency 2 -Queues "agent_plan,notifications"
    .\scripts\dev\start-worker.ps1 -DryRun
#>

param(
    [int] $Concurrency = 4,
    [string] $Queues = "telegram_inbound,agent_plan,agent_execute,memory_index,notifications",
    [int] $ApiTimeout = 420,
    [switch] $DryRun
)

$ErrorActionPreference = "Stop"
Set-Location "F:\dev\agentrouter"

$REDIS_CONTAINER = "amc-dev-redis"
$API_HEALTH_URL = "http://127.0.0.1:8000/health"
$WORKER_DIR = "apps\worker"

# ── helpers ─────────────────────────────────────────────────────────────

function Exit-Fail {
    param([string] $Message)
    Write-Host "[FAIL] $Message"
    exit 1
}

# ── preconditions ───────────────────────────────────────────────────────

# 1. Redis healthy
try {
    $redisPing = docker exec $REDIS_CONTAINER redis-cli ping 2>&1
    if ($LASTEXITCODE -ne 0 -or $redisPing.Trim() -ne "PONG") {
        Exit-Fail "Redis not healthy. Ensure '$REDIS_CONTAINER' is running and returns PONG."
    }
    Write-Host "[INFO] Redis healthy: PONG"
} catch {
    Exit-Fail "Redis container '$REDIS_CONTAINER' not accessible."
}

# 2. API healthy
try {
    $apiHealth = Invoke-RestMethod -Uri $API_HEALTH_URL -TimeoutSec 5 -ErrorAction Stop
    if ($apiHealth.status -ne "ok") {
        Exit-Fail "API /health returned unexpected: $($apiHealth | ConvertTo-Json)"
    }
    Write-Host "[INFO] API healthy at $API_HEALTH_URL"
} catch {
    Exit-Fail "API not healthy at $API_HEALTH_URL. Start API first."
}

# 3. Celery installed
try {
    $celeryCheck = python -c "import celery; print(celery.__version__)" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Exit-Fail "Celery is not installed."
    }
    Write-Host "[INFO] Celery version: $($celeryCheck.Trim())"
} catch {
    Exit-Fail "Celery is not installed."
}

# ── dry-run ─────────────────────────────────────────────────────────────
if ($DryRun) {
    Write-Host ""
    Write-Host "========== Start Worker DryRun =========="
    Write-Host "[DRYRUN] would: verify Redis healthy (docker exec $REDIS_CONTAINER redis-cli ping)"
    Write-Host "[DRYRUN] would: verify API /health=200 at $API_HEALTH_URL"
    Write-Host "[DRYRUN] would: set process-scoped env:"
    Write-Host "    CELERY_BROKER_URL=redis://localhost:6379/1"
    Write-Host "    CELERY_RESULT_BACKEND=redis://localhost:6379/2"
    Write-Host "    API_BASE_URL=http://127.0.0.1:8000"
    Write-Host "    API_TIMEOUT_SECONDS=$ApiTimeout"
    Write-Host "[DRYRUN] would: start celery worker (concurrency=$Concurrency, queues=$Queues) from $WORKER_DIR"
    Write-Host "=========================================="
    Write-Host ""
    exit 0
}

# ── set process-scoped env ──────────────────────────────────────────────
$env:CELERY_BROKER_URL = "redis://localhost:6379/1"
$env:CELERY_RESULT_BACKEND = "redis://localhost:6379/2"
$env:API_BASE_URL = "http://127.0.0.1:8000"
$env:API_TIMEOUT_SECONDS = "$ApiTimeout"

Write-Host "[INFO] Process-scoped env set:"
Write-Host "  CELERY_BROKER_URL = $env:CELERY_BROKER_URL"
Write-Host "  CELERY_RESULT_BACKEND = $env:CELERY_RESULT_BACKEND"
Write-Host "  API_BASE_URL = $env:API_BASE_URL"
Write-Host "  API_TIMEOUT_SECONDS = $env:API_TIMEOUT_SECONDS"

# ── start celery worker ─────────────────────────────────────────────────
Push-Location $WORKER_DIR

Write-Host "[INFO] Starting Celery worker..."
Write-Host "[INFO] Concurrency: $Concurrency"
Write-Host "[INFO] Queues: $Queues"
Write-Host "[INFO] Working dir: $WORKER_DIR"

$workerProcess = Start-Process -FilePath "python" `
    -ArgumentList @(
        "-m", "celery",
        "-A", "app.celery_app",
        "worker",
        "--loglevel=info",
        "--queues=$Queues",
        "--concurrency=$Concurrency"
    ) `
    -PassThru `
    -NoNewWindow

Pop-Location

$pid = $workerProcess.Id
Write-Host "[INFO] Celery worker started. PID: $pid"

# ── report ──────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========== Start Worker Report =========="
Write-Host "  PID          : $pid"
Write-Host "  Concurrency  : $Concurrency"
Write-Host "  Queues       : $Queues"
Write-Host "  Broker       : redis://localhost:6379/1"
Write-Host "  Result       : redis://localhost:6379/2"
Write-Host "  API Base     : http://127.0.0.1:8000"
Write-Host "  API Timeout  : ${ApiTimeout}s"
Write-Host "  Working Dir  : $WORKER_DIR"
Write-Host "=========================================="
Write-Host ""

exit 0
