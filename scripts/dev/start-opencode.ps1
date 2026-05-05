<#
.SYNOPSIS
    BE-11 Runtime Runbook: Start OpenCode server for real runtime provider.

.DESCRIPTION
    Fast-path: if OpenCode is already healthy on 127.0.0.1:4096, prints
    ALREADY_RUNNING and exits 0 immediately.

    Otherwise launches OpenCode via cmd.exe /c start (fully detached, no
    console inheritance). Then polls /global/health and /doc up to 30 s.
    Binds only to 127.0.0.1 (never 0.0.0.0, never port 3001).

.PARAMETER Port
    Port for OpenCode server (default 4096). Binds to 127.0.0.1 only.

.PARAMETER DryRun
    Validate preconditions only, print would-do actions, exit 0.

.EXAMPLE
    .\scripts\dev\start-opencode.ps1
    .\scripts\dev\start-opencode.ps1 -Port 4096
    .\scripts\dev\start-opencode.ps1 -DryRun
#>

param(
    [int] $Port = 4096,
    [switch] $DryRun
)

$ErrorActionPreference = "Stop"
Set-Location "F:\dev\agentrouter"

$HEALTH_URL  = "http://127.0.0.1:${Port}/global/health"
$DOC_URL     = "http://127.0.0.1:${Port}/doc"
$VERIFY_RETRIES  = 30
$VERIFY_DELAY_MS = 1000

# -- helpers -------------------------------------------------------------

function Exit-Fail {
    param([string] $Message)
    Write-Host "[FAIL] $Message"
    exit 1
}

function Resolve-OpenCodeLauncher {
    $appdataNpmPath = Join-Path $env:APPDATA "npm\opencode.cmd"
    if (Test-Path $appdataNpmPath) {
        return $appdataNpmPath
    }
    $fromPath = Get-Command opencode.exe -ErrorAction SilentlyContinue
    if ($fromPath) {
        return $fromPath.Source
    }
    return $null
}

function Test-OpenCodeHealthy {
    try {
        $r = Invoke-RestMethod -Uri $HEALTH_URL -TimeoutSec 5 -ErrorAction Stop
        return ($r.healthy -eq $true)
    } catch {
        return $false
    }
}

function Get-ListenerPid {
    param([int] $TargetPort)
    $conn = Get-NetTCPConnection -State Listen -LocalPort $TargetPort -LocalAddress "127.0.0.1" -ErrorAction SilentlyContinue
    if ($conn) {
        return ($conn | Select-Object -First 1).OwningProcess
    }
    return 0
}

function Kill-StaleOnPort {
    param([int] $TargetPort)
    $connections = Get-NetTCPConnection -LocalPort $TargetPort -LocalAddress "127.0.0.1" -ErrorAction SilentlyContinue
    if (-not $connections) { return }
    $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($p in $pids) {
        $proc = Get-Process -Id $p -ErrorAction SilentlyContinue
        if ($proc) {
            if ($proc.ProcessName -match "^(opencode|node|cmd)$") {
                Write-Host "[INFO] Killing stale '$($proc.ProcessName)' (PID $p) on port $TargetPort"
                Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
                Start-Sleep -Milliseconds 500
            } else {
                Write-Host "[WARN] Port $TargetPort occupied by '$($proc.ProcessName)' (PID $p) - not opencode/node/cmd, skipping"
            }
        }
    }
}

# --- preconditions ---------------------------------------------------------

$opencodePath = Resolve-OpenCodeLauncher
if (-not $opencodePath) {
    Exit-Fail "OpenCode launcher not found. Check %APPDATA%\npm\opencode.cmd or install opencode globally."
}
Write-Host "[INFO] OpenCode launcher: $opencodePath"

# -- fast-path: already running? ------------------------------------------

if ((-not $DryRun) -and (Test-OpenCodeHealthy)) {
    $listenerPid = Get-ListenerPid -TargetPort $Port

    Write-Host ""
    Write-Host "========== Start OpenCode Report =========="
    Write-Host "  Status          : ALREADY_RUNNING"
    Write-Host "  Listen          : 127.0.0.1:$Port"
    if ($listenerPid -gt 0) { Write-Host "  ListenerPID     : $listenerPid" }
    Write-Host "  /global/health  : 200 OK"
    try {
        Invoke-RestMethod -Uri $DOC_URL -TimeoutSec 5 -ErrorAction Stop | Out-Null
        Write-Host "  /doc            : 200 OK"
    } catch {
        Write-Host "  /doc            : NOT ready (health OK was enough)"
    }
    Write-Host "============================================="
    Write-Host ""
    exit 0
}

# -- dry-run -------------------------------------------------------------

if ($DryRun) {
    Write-Host ""
    Write-Host "========== Start OpenCode DryRun =========="
    Write-Host "[DRYRUN] would: resolve launcher (found: $opencodePath)"
    Write-Host "[DRYRUN] would: kill stale opencode/node/cmd processes on port $Port"
    Write-Host "[DRYRUN] would: verify port $Port free on 127.0.0.1"
    Write-Host "[DRYRUN] would: launch via cmd /c start (fully detached, no console inheritance)"
    Write-Host "[DRYRUN] would: poll $HEALTH_URL up to ${VERIFY_RETRIES}s"
    Write-Host "[DRYRUN] would: poll $DOC_URL up to ${VERIFY_RETRIES}s"
    Write-Host "[DRYRUN] would: verify listener only on 127.0.0.1"
    Write-Host "============================================="
    Write-Host ""
    exit 0
}

# -- kill stale -----------------------------------------------------------

Kill-StaleOnPort -TargetPort $Port

# -- verify port free ----------------------------------------------------

$portCheck = Get-NetTCPConnection -LocalPort $Port -LocalAddress "127.0.0.1" -ErrorAction SilentlyContinue
if ($portCheck) {
    Exit-Fail "Port $Port on 127.0.0.1 still occupied after cleanup."
}

# -- clean auth env for child process ------------------------------------

Remove-Item Env:OPENCODE_SERVER_PASSWORD -ErrorAction SilentlyContinue
Remove-Item Env:OPENCODE_SERVER_USERNAME -ErrorAction SilentlyContinue

# -- launch OpenCode fully detached --------------------------------------

Write-Host "[INFO] Launching OpenCode fully detached on 127.0.0.1:$Port ..."

$cmdArgs = @(
    "/c",
    "start",
    '""',                         # empty window title
    "/min",                       # minimized, no focus steal
    "`"$opencodePath`"",          # quoted launcher path
    "serve",
    "--port", "$Port",
    "--hostname", "127.0.0.1"
)

$null = Start-Process -FilePath "cmd.exe" `
    -ArgumentList $cmdArgs `
    -WindowStyle Hidden

Write-Host "[INFO] OpenCode launch command issued. Waiting for startup..."

# -- readiness poll (health -> doc -> listener) ----------------------------

Write-Host "[INFO] Verifying OpenCode endpoints..."
$healthOk = $false
$docOk     = $false

for ($i = 1; $i -le $VERIFY_RETRIES; $i++) {
    Start-Sleep -Milliseconds $VERIFY_DELAY_MS

    if (-not $healthOk) {
        try {
            $hr = Invoke-RestMethod -Uri $HEALTH_URL -TimeoutSec 5 -ErrorAction Stop
            if ($hr.healthy -eq $true) { $healthOk = $true }
        } catch { }
    }

    if ($healthOk -and -not $docOk) {
        try {
            Invoke-RestMethod -Uri $DOC_URL -TimeoutSec 5 -ErrorAction Stop | Out-Null
            $docOk = $true
        } catch { }
    }

    if ($healthOk -and $docOk) { break }
}

# -- verify listener is 127.0.0.1 only -----------------------------------

$bindings = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
$bindsToZero     = $false
$bindsToLocalhost = $false
$listenerPid      = 0
foreach ($b in $bindings) {
    if ($b.LocalAddress -eq "0.0.0.0")   { $bindsToZero = $true }
    if ($b.LocalAddress -eq "127.0.0.1") { $bindsToLocalhost = $true; $listenerPid = $b.OwningProcess }
}

# -- report --------------------------------------------------------------

Write-Host ""
Write-Host "========== Start OpenCode Report =========="
Write-Host "  Listen         : 127.0.0.1:$Port"
if ($listenerPid -gt 0) { Write-Host "  ListenerPID    : $listenerPid" }
Write-Host "  Launcher       : $opencodePath"
Write-Host "  /global/health : $(if ($healthOk) { '200 OK' } else { 'FAIL' })"
Write-Host "  /doc           : $(if ($docOk)    { '200 OK' } else { 'FAIL' })"
Write-Host "  127.0.0.1 only : $(if ($bindsToLocalhost -and -not $bindsToZero) { 'YES' } else { 'WARNING: found 0.0.0.0 binding' })"
Write-Host "============================================="
Write-Host ""

if (-not $healthOk) {
    Exit-Fail "OpenCode readiness failed within ${VERIFY_RETRIES}s. /global/health not healthy."
}

if ($bindsToZero -or -not $bindsToLocalhost) {
    Exit-Fail "Listener validation failed: expected 127.0.0.1 only."
}

exit 0
