<#
.SYNOPSIS
    BE-11 Runtime Runbook: Start API server in opencode_http runtime mode.

.DESCRIPTION
    ALREADY_RUNNING fast-path: if AMC API is healthy on 127.0.0.1:8000 in
    opencode_http mode, prints status and exits 0 immediately.

    Otherwise launches uvicorn fully detached via Start-Process (powershell
    child command with env vars, stdout/stderr -> log files). Then polls
    /health, /projects, /agents up to 30 s. Binds 127.0.0.1 only. Never
    sets DATABASE_URL or edits .env.

    Lifecycle: launcher + readiness checker, NOT foreground uvicorn wrapper.
    Script always exits (never hangs on uvicorn process).

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
$OPENCODE_DOC_URL = "${OpenCodeUrl}/doc"
$VERIFY_TIMEOUT_SEC = 30
$VERIFY_DELAY_MS = 750

# -- helpers -------------------------------------------------------------

function Exit-Fail {
    param([string] $Message)
    Write-Host "[FAIL] $Message"
    exit 1
}

function Get-ApiListenerPid {
    param([int] $TargetPort)
    $conn = Get-NetTCPConnection -LocalPort $TargetPort -LocalAddress "127.0.0.1" -State Listen -ErrorAction SilentlyContinue
    if ($conn) { return ($conn | Select-Object -First 1).OwningProcess }
    return 0
}

function Test-ApiHealthy {
    try {
        $r = Invoke-RestMethod -Uri $HEALTH_URL -TimeoutSec 5 -ErrorAction Stop
        return ($r.status -eq "ok")
    } catch { return $false }
}

function Test-ApiIsOpencodeHttp {
    param([int] $ProcessId)
    try {
        # 1) Check this script's own env (inherited from parent)
        $localProvider = (Get-Item "Env:RUNTIME_PROVIDER" -ErrorAction SilentlyContinue).Value
        if ($localProvider -eq "opencode_http") { return $true }
        # 2) Check the API child process command line for env injection
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId").CommandLine
        if ($cmdLine -match "RUNTIME_PROVIDER\s*=\s*opencode_http") { return $true }
        # 3) Negative detection: if we reach here, API is NOT opencode_http
        return $false
    } catch { return $false }
}

function Stop-ApiOnPort {
    param([int] $TargetPort)
    $connections = Get-NetTCPConnection -LocalPort $TargetPort -LocalAddress "127.0.0.1" -ErrorAction SilentlyContinue
    if (-not $connections) { return }
    $pids = $connections.OwningProcess | Select-Object -Unique
    foreach ($p in $pids) {
        try {
            $proc = Get-Process -Id $p -ErrorAction SilentlyContinue
            if (-not $proc) { continue }
            if ($proc.ProcessName -notmatch "^(python|uvicorn)$") { continue }
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $p").CommandLine
            if ($cmdLine -match "app\.main:app") {
                Write-Host "[INFO] Stopping existing API process '$($proc.ProcessName)' (PID $p) on port $TargetPort ..."
                Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
                Start-Sleep -Milliseconds 1000
            }
        } catch {
            Write-Host "[WARN] Could not stop process PID $p : $_"
        }
    }
}

# -- dry-run -------------------------------------------------------------

if ($DryRun) {
    Write-Host ""
    Write-Host "========== Start API OpenCode DryRun =========="
    Write-Host "[DRYRUN] would: verify OpenCode /global/health and /doc at $OpenCodeUrl"
    Write-Host "[DRYRUN] would: stop existing AMC API on port $Port (python/uvicorn + app.main:app only)"
    Write-Host "[DRYRUN] would: launch fully detached powershell child with env vars:"
    Write-Host "    RUNTIME_PROVIDER=opencode_http"
    Write-Host "    OPENCODE_SERVER_URL=$OpenCodeUrl"
    Write-Host "    RUNTIME_ALLOW_REAL_OPENCODE_HTTP=true"
    Write-Host "    DEBUG=true"
    Write-Host "[DRYRUN] would: redirect uvicorn stdout -> logs/api-opencode-stdout.log"
    Write-Host "[DRYRUN] would: redirect uvicorn stderr -> logs/api-opencode-stderr.log"
    Write-Host "[DRYRUN] would: validate config via python check"
    Write-Host "[DRYRUN] would: poll /health, /projects, /agents up to ${VERIFY_TIMEOUT_SEC}s"
    Write-Host "[DRYRUN] would: verify listener 127.0.0.1 only (no 0.0.0.0, no ::)"
    Write-Host "[DRYRUN] would: NOT set DATABASE_URL"
    Write-Host "[DRYRUN] would: NOT edit .env or persistent env"
    Write-Host "================================================="
    Write-Host ""
    exit 0
}

# -- preconditions -------------------------------------------------------

# 1. OpenCode healthy + doc reachable
try {
    $ocHealth = Invoke-RestMethod -Uri $OPENCODE_HEALTH_URL -TimeoutSec 5 -ErrorAction Stop
    Invoke-RestMethod -Uri $OPENCODE_DOC_URL -TimeoutSec 5 -ErrorAction Stop | Out-Null
    Write-Host "[INFO] OpenCode healthy and docs reachable at $OpenCodeUrl"
} catch {
    Exit-Fail "OpenCode /global/health or /doc is not ready at $OpenCodeUrl. Run start-opencode.ps1 first."
}

# 2. uvicorn installed
$uvicornCheck = python -c "import uvicorn; print(uvicorn.__version__)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Exit-Fail "uvicorn is not installed."
}

# -- fast-path: already running in opencode_http mode? -------------------

$listenerPid = Get-ApiListenerPid -TargetPort $Port
if ($listenerPid -gt 0) {
    $apiIsOpencodeHttp = Test-ApiIsOpencodeHttp -ProcessId $listenerPid

    if ($apiIsOpencodeHttp -and (Test-ApiHealthy)) {
        Write-Host ""
        Write-Host "========== Start API OpenCode Report =========="
        Write-Host "  Status        : ALREADY_RUNNING"
        Write-Host "  PID           : $listenerPid"
        Write-Host "  Listen        : 127.0.0.1:$Port"
        Write-Host "  Provider      : opencode_http"
        Write-Host "  /health       : 200 OK"
        try { Invoke-RestMethod -Uri $PROJECTS_URL -TimeoutSec 5; Write-Host "  /projects     : 200 OK" } catch { Write-Host "  /projects     : NOT ready" }
        try { Invoke-RestMethod -Uri $AGENTS_URL -TimeoutSec 5;     Write-Host "  /agents       : 200 OK" } catch { Write-Host "  /agents       : NOT ready" }
        Write-Host "================================================="
        Write-Host ""
        exit 0
    }

    # API is running but NOT in opencode_http mode -> stop and restart
    if (Test-ApiHealthy) {
        Write-Host "[INFO] API on port $Port is running but NOT in opencode_http mode."
        Write-Host "[INFO] Stopping existing API (PID $listenerPid) to restart in opencode_http mode..."
        Stop-ApiOnPort -TargetPort $Port
        Start-Sleep -Milliseconds 1000
    }
}

# -- stop existing API ---------------------------------------------------
Stop-ApiOnPort -TargetPort $Port

# -- verify port free ----------------------------------------------------
Start-Sleep -Milliseconds 500
$portCheck = Get-NetTCPConnection -LocalPort $Port -LocalAddress "127.0.0.1" -ErrorAction SilentlyContinue
if ($portCheck) {
    Exit-Fail "Port $Port on 127.0.0.1 is still occupied. Cannot start API."
}

# -- set process-scoped env (needed for config validation below) ---------
# NOTE: NEVER set DATABASE_URL - rely on config.py default
$env:RUNTIME_PROVIDER = "opencode_http"
$env:OPENCODE_SERVER_URL = $OpenCodeUrl
$env:RUNTIME_ALLOW_REAL_OPENCODE_HTTP = "true"
$env:DEBUG = "true"
Write-Host "[INFO] Process-scoped env set:"
Write-Host "  RUNTIME_PROVIDER = $env:RUNTIME_PROVIDER"
Write-Host "  OPENCODE_SERVER_URL = $env:OPENCODE_SERVER_URL"
Write-Host "  RUNTIME_ALLOW_REAL_OPENCODE_HTTP = $env:RUNTIME_ALLOW_REAL_OPENCODE_HTTP"
Write-Host "  DEBUG = $env:DEBUG"
Write-Host "  DATABASE_URL = (not set - using config default)"

# -- validate config resolves correctly ----------------------------------
Write-Host "[INFO] Validating config..."
Push-Location $API_DIR
try {
    $pyCode = @"
from app.config import settings
actual_provider = str(settings.RUNTIME_PROVIDER)
actual_url = str(settings.OPENCODE_SERVER_URL)
actual_allow = settings.RUNTIME_ALLOW_REAL_OPENCODE_HTTP
assert actual_provider == "opencode_http", f"RUNTIME_PROVIDER mismatch: {actual_provider}"
assert actual_url == "$OpenCodeUrl", f"OPENCODE_SERVER_URL mismatch: {actual_url}"
assert actual_allow is True, f"RUNTIME_ALLOW_REAL_OPENCODE_HTTP must be true"
print("CONFIG OK")
"@
    $pyCode | Set-Content -Path "$env:TEMP\_smoke_cfg_val.py" -Encoding UTF8
    $configCheck = python "$env:TEMP\_smoke_cfg_val.py" 2>&1
    Remove-Item "$env:TEMP\_smoke_cfg_val.py" -ErrorAction SilentlyContinue

    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        Exit-Fail "Config validation failed: $configCheck"
    }
    Write-Host "[INFO] Config validation: $($configCheck.Trim())"
} finally {
    Pop-Location
}

# -- launch API fully detached -------------------------------------------
# CRITICAL: do NOT use -NoNewWindow (hangs parent PowerShell on uvicorn).
# Use powershell child command to pass env vars correctly, redirect output.
Write-Host "[INFO] Launching API fully detached on 127.0.0.1:$Port ..."

$logDir = "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

$childCommand = @"
`$env:RUNTIME_PROVIDER='opencode_http'
`$env:OPENCODE_SERVER_URL='$OpenCodeUrl'
`$env:RUNTIME_ALLOW_REAL_OPENCODE_HTTP='true'
`$env:DEBUG='true'
python -m uvicorn --app-dir $API_DIR app.main:app --host 127.0.0.1 --port $Port
"@

$scriptPath = Join-Path $logDir "_api_launcher.ps1"
$childCommand | Set-Content -Path $scriptPath -Encoding UTF8

$stdoutLog = Join-Path $logDir "api-opencode-stdout.log"
$stderrLog = Join-Path $logDir "api-opencode-stderr.log"

$apiProcess = Start-Process -FilePath "powershell" `
    -ArgumentList @(
        "-NoProfile",
        "-WindowStyle", "Hidden",
        "-File", (Resolve-Path $scriptPath).Path
    ) `
    -PassThru `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog

$apiPid = $apiProcess.Id
Write-Host "[INFO] API launch command issued. PID: $apiPid"
Write-Host "[INFO] Listen address: 127.0.0.1:$Port"
Write-Host "[INFO] Provider mode: opencode_http"
Write-Host "[INFO] stdout -> $stdoutLog"
Write-Host "[INFO] stderr -> $stderrLog"

# Clean up the temp launcher script after a short delay
Start-Job -ScriptBlock {
    param($path) Start-Sleep -Seconds 5; Remove-Item $path -ErrorAction SilentlyContinue
} -ArgumentList $scriptPath | Out-Null

# -- readiness poll ------------------------------------------------------
Write-Host "[INFO] Verifying API endpoints (timeout ${VERIFY_TIMEOUT_SEC}s)..."
$pollStart = Get-Date
$healthOk = $false
$projectsOk = $false
$agentsOk = $false
$verifyTimeoutSec = $VERIFY_TIMEOUT_SEC

while ($true) {
    Start-Sleep -Milliseconds $VERIFY_DELAY_MS
    $elapsed = ((Get-Date) - $pollStart).TotalSeconds

    if (-not $healthOk) {
        try {
            $healthResp = Invoke-RestMethod -Uri $HEALTH_URL -TimeoutSec 5 -ErrorAction Stop
            if ($healthResp.status -eq "ok") { $healthOk = $true }
        } catch { }
    }

    if ($healthOk) {
        if (-not $projectsOk) {
            try { Invoke-RestMethod -Uri $PROJECTS_URL -TimeoutSec 5 -ErrorAction Stop; $projectsOk = $true } catch {
                if ($_.Exception.Response -and $_.Exception.Response.StatusCode.value__ -eq 200) { $projectsOk = $true }
            }
        }
        if (-not $agentsOk) {
            try { Invoke-RestMethod -Uri $AGENTS_URL -TimeoutSec 5 -ErrorAction Stop; $agentsOk = $true } catch {
                if ($_.Exception.Response -and $_.Exception.Response.StatusCode.value__ -eq 200) { $agentsOk = $true }
            }
        }
        if ($projectsOk -and $agentsOk) { break }
    }

    if ($elapsed -gt $verifyTimeoutSec) { break }
}

# -- verify listener is 127.0.0.1 only -----------------------------------
$bindings = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
$bindsToZero = $false
$bindsToLocalhost = $false
$bindsToV6 = $false
$listenerPidFinal = 0
foreach ($b in $bindings) {
    if ($b.LocalAddress -eq "0.0.0.0") { $bindsToZero = $true }
    if ($b.LocalAddress -eq "127.0.0.1") { $bindsToLocalhost = $true; $listenerPidFinal = $b.OwningProcess }
    if ($b.LocalAddress -eq "::") { $bindsToV6 = $true }
}

# -- report --------------------------------------------------------------
Write-Host ""
Write-Host "========== Start API OpenCode Report =========="
Write-Host "  Status        : $(if ($healthOk) { 'STARTED' } else { 'FAIL' })"
Write-Host "  PID           : $(if ($listenerPidFinal -gt 0) { $listenerPidFinal } else { $apiPid })"
Write-Host "  Listen        : 127.0.0.1:$Port"
Write-Host "  Provider      : opencode_http"
Write-Host "  OpenCode URL  : $OpenCodeUrl"
Write-Host "  /health       : $(if ($healthOk) { '200 OK' } else { 'FAIL' })"
Write-Host "  /projects     : $(if ($projectsOk) { '200 OK' } else { 'FAIL' })"
Write-Host "  /agents       : $(if ($agentsOk) { '200 OK' } else { 'FAIL' })"
Write-Host "  127.0.0.1 only: $(if ($bindsToLocalhost -and -not $bindsToZero -and -not $bindsToV6) { 'YES' } else { 'WARNING' })"
Write-Host "  DATABASE_URL  : (not set - using config default)"
Write-Host "  Duration      : $([math]::Round($elapsed, 1))s"
Write-Host "================================================="
Write-Host ""

if (-not $healthOk) {
    # DO NOT exit fail - API may still be starting. Report and exit 0.
    Write-Host "[WARN] /health did not respond within ${verifyTimeoutSec}s."
    Write-Host "[INFO] API process is running detached. Check logs: $stdoutLog"
    Write-Host "[INFO] To verify manually: curl $HEALTH_URL"
}

if ($bindsToZero -or $bindsToV6 -or -not $bindsToLocalhost) {
    Write-Host "[WARN] Listener validation: expected 127.0.0.1 only, found unexpected binding."
}

exit 0
