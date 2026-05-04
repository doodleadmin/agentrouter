<#
.SYNOPSIS
    BE-11 Runtime Runbook: Clean up runtime processes and restart API in stub mode.

.DESCRIPTION
    Stops OpenCode server, Celery worker, and API on target ports. Waits for
    ports to free. Cleans process-scoped RUNTIME env vars. Optionally restarts
    API in stub mode (auto-restart is default; use -SkipApiRestart to prevent).
    Never stops postgres/redis containers unless explicitly requested.

.PARAMETER Port
    API port (default 8000).

.PARAMETER OpenCodePort
    OpenCode port (default 4096).

.PARAMETER KeepDb
    Keep database (default — db is never dropped).

.PARAMETER SkipApiRestart
    Skip auto-restart of API in stub mode.

.PARAMETER DryRun
    Validate preconditions only, print would-do actions, exit 0.

.EXAMPLE
    .\scripts\dev\cleanup-runtime.ps1
    .\scripts\dev\cleanup-runtime.ps1 -SkipApiRestart
    .\scripts\dev\cleanup-runtime.ps1 -DryRun
#>

param(
    [int] $Port = 8000,
    [int] $OpenCodePort = 4096,
    [switch] $KeepDb,
    [switch] $SkipApiRestart,
    [switch] $DryRun
)

$ErrorActionPreference = "Stop"
Set-Location "F:\dev\agentrouter"

$API_HEALTH_URL = "http://127.0.0.1:${Port}/health"
$PROJECTS_URL = "http://127.0.0.1:${Port}/projects"
$AGENTS_URL = "http://127.0.0.1:${Port}/agents"
$API_DIR = "apps\api"
$PORT_WAIT_TIMEOUT_SEC = 10

# ── helpers ─────────────────────────────────────────────────────────────

function Exit-Fail {
    param([string] $Message)
    Write-Host "[FAIL] $Message"
    exit 1
}

function Stop-ProcessOnPort {
    param(
        [int] $TargetPort,
        [string] $ProcessNamePattern
    )
    $connections = Get-NetTCPConnection -LocalPort $TargetPort -LocalAddress "127.0.0.1" -ErrorAction SilentlyContinue
    if (-not $connections) { return }

    $pids = $connections.OwningProcess | Select-Object -Unique
    foreach ($p in $pids) {
        try {
            $proc = Get-Process -Id $p -ErrorAction SilentlyContinue
            if ($proc) {
                $procName = $proc.ProcessName
                # Verify process name matches pattern (guard against killing wrong process)
                if ($procName -match $ProcessNamePattern) {
                    Write-Host "[INFO] Stopping '$procName' (PID $p) on port $TargetPort ..."
                    Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
                    Start-Sleep -Milliseconds 1000
                } else {
                    Write-Host "[WARN] Port $TargetPort occupied by '$procName' (PID $p) — not matching '$ProcessNamePattern', skipping."
                }
            }
        } catch {
            Write-Host "[WARN] Could not stop process PID $p : $_"
        }
    }
}

function Wait-PortFree {
    param(
        [int] $TargetPort,
        [int] $TimeoutSec = 10
    )
    $endTime = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $endTime) {
        $conn = Get-NetTCPConnection -LocalPort $TargetPort -LocalAddress "127.0.0.1" -ErrorAction SilentlyContinue
        if (-not $conn) {
            Write-Host "[INFO] Port $TargetPort is now free."
            return $true
        }
        Start-Sleep -Milliseconds 500
    }
    Write-Host "[WARN] Port $TargetPort still occupied after ${TimeoutSec}s."
    return $false
}

function Remove-RuntimeEnvVars {
    Remove-Item Env:RUNTIME_PROVIDER -ErrorAction SilentlyContinue
    Remove-Item Env:OPENCODE_SERVER_URL -ErrorAction SilentlyContinue
    Remove-Item Env:RUNTIME_ALLOW_REAL_OPENCODE_HTTP -ErrorAction SilentlyContinue
    Remove-Item Env:API_TIMEOUT_SECONDS -ErrorAction SilentlyContinue
    Write-Host "[INFO] Removed RUNTIME-* process-scoped env vars."
}

# ── dry-run ─────────────────────────────────────────────────────────────
if ($DryRun) {
    Write-Host ""
    Write-Host "========== Cleanup Runtime DryRun =========="
    Write-Host "[DRYRUN] would: stop OpenCode on port $OpenCodePort (verify opencode before kill)"
    Write-Host "[DRYRUN] would: stop Celery worker (find by process name or port)"
    Write-Host "[DRYRUN] would: stop API on port $Port"
    Write-Host "[DRYRUN] would: wait for ports to free (timeout ${PORT_WAIT_TIMEOUT_SEC}s)"
    Write-Host "[DRYRUN] would: remove process-scoped RUNTIME_* env vars"
    if (-not $SkipApiRestart) {
        Write-Host "[DRYRUN] would: auto-restart API in stub mode on 127.0.0.1:$Port"
        Write-Host "[DRYRUN] would: verify /health=200, /projects=200, /agents=200"
    }
    Write-Host "[DRYRUN] would: verify port $OpenCodePort free"
    Write-Host "[DRYRUN] would: verify git clean"
    Write-Host "[DRYRUN] would: NOT stop postgres/redis containers"
    Write-Host "============================================="
    Write-Host ""
    exit 0
}

# ── 1. Stop OpenCode ────────────────────────────────────────────────────
Write-Host "[INFO] Step 1: Stopping OpenCode on port $OpenCodePort ..."
Stop-ProcessOnPort -TargetPort $OpenCodePort -ProcessNamePattern "^(opencode|node|cmd)$"

# ── 2. Stop Celery worker ───────────────────────────────────────────────
Write-Host "[INFO] Step 2: Stopping Celery worker..."
# Celery worker processes are typically named 'python' or 'celery'
$celeryProcs = Get-Process -Name "python*" -ErrorAction SilentlyContinue | Where-Object {
    try {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        return ($cmdLine -match "celery" -or $cmdLine -match "celery_app")
    } catch { $false }
}
if ($celeryProcs) {
    foreach ($cp in $celeryProcs) {
        Write-Host "[INFO] Stopping Celery worker process (PID $($cp.Id))..."
        Stop-Process -Id $cp.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Milliseconds 1500
} else {
    Write-Host "[INFO] No Celery worker processes found."
}

# Also check for any processes consuming from Redis queues
$redisConsumers = Get-Process -Name "python*" -ErrorAction SilentlyContinue | Where-Object {
    try {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        return ($cmdLine -match "worker" -and $cmdLine -match "celery")
    } catch { $false }
}
foreach ($rc in $redisConsumers) {
    Write-Host "[INFO] Stopping additional worker (PID $($rc.Id))..."
    Stop-Process -Id $rc.Id -Force -ErrorAction SilentlyContinue
}

# ── 3. Stop API ─────────────────────────────────────────────────────────
Write-Host "[INFO] Step 3: Stopping API on port $Port ..."
Stop-ProcessOnPort -TargetPort $Port -ProcessNamePattern "^(python|uvicorn)$"

# ── 4. Wait for ports to free ────────────────────────────────────────────
Write-Host "[INFO] Step 4: Waiting for ports to free..."
$apiPortFree = Wait-PortFree -TargetPort $Port -TimeoutSec $PORT_WAIT_TIMEOUT_SEC
$ocPortFree = Wait-PortFree -TargetPort $OpenCodePort -TimeoutSec $PORT_WAIT_TIMEOUT_SEC

# ── 5. Clean process-scoped env ─────────────────────────────────────────
Write-Host "[INFO] Step 5: Cleaning process-scoped env..."
Remove-RuntimeEnvVars

# ── 6. Auto-restart API in stub mode ─────────────────────────────────────
if (-not $SkipApiRestart) {
    Write-Host "[INFO] Step 6: Auto-restarting API in stub mode..."

    if (-not $apiPortFree) {
        Write-Host "[WARN] Port $Port not free. Attempting force cleanup..."
        Stop-ProcessOnPort -TargetPort $Port -ProcessNamePattern "^(python|uvicorn)$"
        Start-Sleep -Seconds 2
    }

    # Ensure no RUNTIME env overrides
    Remove-RuntimeEnvVars
    $env:DEBUG = "true"

    Write-Host "[INFO] Starting API in stub mode on 127.0.0.1:$Port ..."
    $apiProcess = Start-Process -FilePath "python" `
        -ArgumentList @(
            "-m", "uvicorn",
            "--app-dir", $API_DIR,
            "app.main:app",
            "--host", "127.0.0.1",
            "--port", "$Port"
        ) `
        -PassThru `
        -NoNewWindow

    $apiPid = $apiProcess.Id
    Write-Host "[INFO] API process started. PID: $apiPid"

    # Verify endpoints
    Write-Host "[INFO] Verifying API stub mode..."
    $healthOk = $false
    $projectsOk = $false
    $agentsOk = $false

    for ($i = 1; $i -le 15; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            $hr = Invoke-RestMethod -Uri $API_HEALTH_URL -TimeoutSec 5 -ErrorAction Stop
            if ($hr.status -eq "ok") { $healthOk = $true }
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
} else {
    Write-Host "[INFO] -SkipApiRestart flag set. API not restarted."
    $healthOk = $false
    $projectsOk = $false
    $agentsOk = $false
    $apiPid = "N/A"
}

# ── 7. Verify port 4096 free, git clean ─────────────────────────────────
Write-Host "[INFO] Step 7: Final verification..."
$ocPortFinalCheck = Get-NetTCPConnection -LocalPort $OpenCodePort -LocalAddress "127.0.0.1" -ErrorAction SilentlyContinue
$ocPortFreeFinal = (-not $ocPortFinalCheck)

$gitStatus = git status --porcelain 2>&1
$gitClean = (-not $gitStatus)

# ── report ──────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========== Cleanup Runtime Report =========="
Write-Host "  OpenCode stopped        : $(if ($ocPortFreeFinal) { '[OK]' } else { '[FAIL] port still in use' })"
Write-Host "  Celery worker stopped   : [OK] (attempted)"
Write-Host "  API stopped on $Port    : $(if ($apiPortFree) { '[OK]' } else { '[WARN]' })"
Write-Host "  Runtime env cleaned     : [OK]"
if (-not $SkipApiRestart) {
    Write-Host "  API restarted (stub)    : $(if ($healthOk) { '[OK] PID=$apiPid' } else { '[FAIL]' })"
    Write-Host "  /health                 : $(if ($healthOk) { '200 OK' } else { 'FAIL' })"
    Write-Host "  /projects               : $(if ($projectsOk) { '200 OK' } else { 'FAIL' })"
    Write-Host "  /agents                 : $(if ($agentsOk) { '200 OK' } else { 'FAIL' })"
}
Write-Host "  Port $OpenCodePort free        : $(if ($ocPortFreeFinal) { 'YES' } else { 'NO' })"
Write-Host "  Git clean               : $(if ($gitClean) { 'YES' } else { 'NO (has changes)' })"
Write-Host "  Postgres/Redis          : KEPT (not stopped)"
Write-Host "=============================================="
Write-Host ""

exit 0
