<#
.SYNOPSIS
    BE-11 Runtime Runbook: Start OpenCode server for real runtime provider.

.DESCRIPTION
    Resolves the opencode launcher dynamically (prefers %APPDATA%\npm\opencode.cmd,
    fallback to opencode.exe from PATH). Kills stale opencode/node processes on
    the target port. Starts opencode serve on 127.0.0.1 only.
    Verifies /global/health=200 and /doc=200.

.PARAMETER Port
    Port for OpenCode server (default 4096). Only binds to 127.0.0.1.

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

$HEALTH_URL = "http://127.0.0.1:${Port}/global/health"
$DOC_URL = "http://127.0.0.1:${Port}/doc"
$VERIFY_RETRIES = 20
$VERIFY_DELAY_MS = 500

# ── helpers ─────────────────────────────────────────────────────────────

function Exit-Fail {
    param([string] $Message)
    Write-Host "[FAIL] $Message"
    exit 1
}

function Resolve-OpenCodeLauncher {
    # Prefer: %APPDATA%\npm\opencode.cmd
    $appdataNpmPath = Join-Path $env:APPDATA "npm\opencode.cmd"
    if (Test-Path $appdataNpmPath) {
        return $appdataNpmPath
    }

    # Fallback: opencode.exe from PATH
    $fromPath = Get-Command opencode.exe -ErrorAction SilentlyContinue
    if ($fromPath) {
        return $fromPath.Source
    }

    # Never use opencode.ps1
    return $null
}

function Kill-StaleOnPort {
    param([int] $TargetPort)
    $connections = Get-NetTCPConnection -LocalPort $TargetPort -LocalAddress "127.0.0.1" -ErrorAction SilentlyContinue
    if ($connections) {
        $uniquePids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($p in $uniquePids) {
            $proc = Get-Process -Id $p -ErrorAction SilentlyContinue
            if ($proc -and $proc.ProcessName -match "^(opencode|node)$") {
                Write-Host "[INFO] Killing stale process '$($proc.ProcessName)' (PID $p) on port $TargetPort"
                Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
                Start-Sleep -Milliseconds 500
            } elseif ($proc) {
                Write-Host "[WARN] Port $TargetPort occupied by '$($proc.ProcessName)' (PID $p) - not opencode/node, skipping"
            }
        }
    }
}

# ── preconditions ───────────────────────────────────────────────────────

# 1. Resolve opencode launcher
$opencodePath = Resolve-OpenCodeLauncher
if (-not $opencodePath) {
    Exit-Fail "OpenCode launcher not found. Check %APPDATA%\npm\opencode.cmd or install opencode globally."
}
Write-Host "[INFO] OpenCode launcher: $opencodePath"

# ── dry-run ─────────────────────────────────────────────────────────────
if ($DryRun) {
    Write-Host ""
    Write-Host "========== Start OpenCode DryRun =========="
    Write-Host "[DRYRUN] would: resolve launcher (found: $opencodePath)"
    Write-Host "[DRYRUN] would: kill stale opencode/node processes on port $Port"
    Write-Host "[DRYRUN] would: verify port $Port free on 127.0.0.1"
    Write-Host "[DRYRUN] would: clean auth env vars from child process"
    Write-Host "[DRYRUN] would: start 'opencode serve --port $Port --hostname 127.0.0.1'"
    Write-Host "[DRYRUN] would: verify $HEALTH_URL -> 200"
    Write-Host "[DRYRUN] would: verify $DOC_URL -> 200"
    Write-Host "[DRYRUN] would: verify listener only on 127.0.0.1"
    Write-Host "============================================="
    Write-Host ""
    exit 0
}

# ── kill stale ───────────────────────────────────────────────────────────
Kill-StaleOnPort -TargetPort $Port

# ── verify port free ────────────────────────────────────────────────────
$portCheck = Get-NetTCPConnection -LocalPort $Port -LocalAddress "127.0.0.1" -ErrorAction SilentlyContinue
if ($portCheck) {
    Exit-Fail "Port $Port on 127.0.0.1 is still occupied after cleanup."
}

# ── clean auth env for child process ────────────────────────────────────
Remove-Item Env:OPENCODE_SERVER_PASSWORD -ErrorAction SilentlyContinue
Remove-Item Env:OPENCODE_SERVER_USERNAME -ErrorAction SilentlyContinue

# ── start opencode ──────────────────────────────────────────────────────
Write-Host "[INFO] Starting OpenCode server on 127.0.0.1:$Port ..."

# Determine how to launch
if ($opencodePath -match "\.cmd$") {
    $openCodeProcess = Start-Process -FilePath "cmd.exe" `
        -ArgumentList "/c", "`"$opencodePath`" serve --port $Port --hostname 127.0.0.1" `
        -PassThru `
        -NoNewWindow
} else {
    $openCodeProcess = Start-Process -FilePath $opencodePath `
        -ArgumentList "serve", "--port", "$Port", "--hostname", "127.0.0.1" `
        -PassThru `
        -NoNewWindow
}

$ocPid = $openCodeProcess.Id
Write-Host "[INFO] OpenCode process started. PID: $ocPid"
Write-Host "[INFO] Listen address: 127.0.0.1:$Port"

# ── verify endpoints ────────────────────────────────────────────────────
Write-Host "[INFO] Verifying OpenCode endpoints..."
$healthOk = $false
$docOk = $false

for ($i = 1; $i -le $VERIFY_RETRIES; $i++) {
    Start-Sleep -Milliseconds $VERIFY_DELAY_MS

    try {
        $healthResp = Invoke-RestMethod -Uri $HEALTH_URL -TimeoutSec 5 -ErrorAction Stop
        $healthOk = $true
    } catch {
        # still starting
    }

    if ($healthOk) {
        try {
            $docResp = Invoke-RestMethod -Uri $DOC_URL -TimeoutSec 5 -ErrorAction Stop
            $docOk = $true
        } catch {
            # may not be ready
        }
        if ($docOk) {
            break
        }
    }
}

# ── verify listener is 127.0.0.1 only ───────────────────────────────────
$bindings = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
$bindsToZero = $false
$bindsToLocalhost = $false
foreach ($b in $bindings) {
    if ($b.LocalAddress -eq "0.0.0.0") { $bindsToZero = $true }
    if ($b.LocalAddress -eq "127.0.0.1") { $bindsToLocalhost = $true }
}

# ── report ──────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========== Start OpenCode Report =========="
Write-Host "  PID            : $ocPid"
Write-Host "  Listen         : 127.0.0.1:$Port"
Write-Host "  Launcher       : $opencodePath"
Write-Host "  /global/health : $(if ($healthOk) { '200 OK' } else { 'FAIL' })"
Write-Host "  /doc           : $(if ($docOk) { '200 OK' } else { 'FAIL' })"
Write-Host "  127.0.0.1 only : $(if ($bindsToLocalhost -and -not $bindsToZero) { 'YES' } else { 'WARNING: found 0.0.0.0 binding' })"
Write-Host "============================================="
Write-Host ""

if (-not $healthOk -or -not $docOk) {
    Write-Host "[WARN] OpenCode may still be starting. Try checking manually."
}

exit 0
