<#
.SYNOPSIS
    BE-11 Runtime Runbook: Smoke test for stub runtime provider (plan-only).

.DESCRIPTION
    Verifies that the stub (plan-only) runtime provider works correctly:
    - API must be running in stub mode (RUNTIME_PROVIDER=stub)
    - Creates project, agent, and low-risk task
    - Calls POST /runtime/tasks/{id}/plan directly (bypassing worker)
    - Verifies approved status, stub-session session_id, plan_generated event
    - Verifies NO code execution, file changes, sandbox events, or runtime errors
    - Verifies git stays clean

.PARAMETER DryRun
    Validate preconditions only, print would-do actions, exit 0.

.EXAMPLE
    .\scripts\dev\smoke-stub-runtime.ps1
    .\scripts\dev\smoke-stub-runtime.ps1 -DryRun
#>

param(
    [switch] $DryRun
)

$ErrorActionPreference = "Stop"
Set-Location "F:\dev\agentrouter"

$API_BASE = "http://127.0.0.1:8000"
$TIMESTAMP = Get-Date -Format "yyyyMMdd-HHmmss"
$PROJECT_SLUG = "smoke-stub-$TIMESTAMP"
$AGENT_SLUG = "smoke-agent-$TIMESTAMP"

# ── helpers ─────────────────────────────────────────────────────────────

function Exit-Fail {
    param([string] $Message)
    Write-Host "[FAIL] $Message"
    exit 1
}

function Invoke-Api {
    param(
        [string] $Method,
        [string] $Uri,
        $Body,
        [int] $TimeoutSec = 120
    )
    $params = @{
        Uri         = $Uri
        Method      = $Method
        ContentType = "application/json"
        TimeoutSec  = $TimeoutSec
    }
    if ($Body) {
        $params.Body = ($Body | ConvertTo-Json -Depth 10)
    }
    return Invoke-RestMethod @params
}

# ── preconditions ───────────────────────────────────────────────────────

# 1. API healthy
try {
    $health = Invoke-RestMethod -Uri "$API_BASE/health" -TimeoutSec 5 -ErrorAction Stop
    if ($health.status -ne "ok") {
        Exit-Fail "API not healthy at $API_BASE"
    }
    Write-Host "[INFO] API healthy at $API_BASE"
} catch {
    Exit-Fail "API not reachable at $API_BASE/health"
}

# 2. API running in stub mode
try {
    $providers = Invoke-RestMethod -Uri "$API_BASE/runtime/providers" -TimeoutSec 5 -ErrorAction Stop
    # Check if we can detect stub; if endpoint doesn't exist, proceed anyway
    Write-Host "[INFO] Runtime providers: $($providers | ConvertTo-Json -Depth 1)"
} catch {
    # Endpoint may not exist; skip check
    Write-Host "[INFO] /runtime/providers endpoint not available, assuming stub (check start-api-stub.ps1 was used)"
}

# Must detect stub mode — if API is in opencode_http mode, this smoke test would fail
try {
    $healthResp = Invoke-RestMethod -Uri "$API_BASE/health" -TimeoutSec 5
    Write-Host "[INFO] API mode check: will verify stub behavior via session_id"
} catch {
    Exit-Fail "Cannot reach API."
}

# 3. Git clean
$gitStatus = git status --porcelain 2>&1
if ($LASTEXITCODE -ne 0) {
    Exit-Fail "Git status failed. Ensure you are in a git repository."
}
if ($gitStatus) {
    Exit-Fail "Git working tree is dirty. Please commit or stash changes before running smoke test."
}
Write-Host "[INFO] Git status: clean"

# ── dry-run ─────────────────────────────────────────────────────────────
if ($DryRun) {
    Write-Host ""
    Write-Host "========== Smoke Stub Runtime DryRun =========="
    Write-Host "[DRYRUN] would: verify API in stub mode"
    Write-Host "[DRYRUN] would: verify git clean"
    Write-Host "[DRYRUN] would: create project   slug=$PROJECT_SLUG"
    Write-Host "[DRYRUN] would: create agent     slug=$AGENT_SLUG"
    Write-Host "[DRYRUN] would: create task      risk_level=low"
    Write-Host "[DRYRUN] would: POST /runtime/tasks/{id}/plan (timeout 120s)"
    Write-Host "[DRYRUN] would: PRINT prominently: Worker bypass: direct POST /runtime used."
    Write-Host "[DRYRUN] would: verify status=approved"
    Write-Host "[DRYRUN] would: verify session_id=stub-session"
    Write-Host "[DRYRUN] would: verify plan_generated count=1"
    Write-Host "[DRYRUN] would: verify no runtime_error, policy_blocked, command/file/sandbox events"
    Write-Host "[DRYRUN] would: verify git still clean"
    Write-Host "================================================"
    Write-Host ""
    exit 0
}

# ── create project ──────────────────────────────────────────────────────
Write-Host "[INFO] Creating project '$PROJECT_SLUG' ..."
try {
    $project = Invoke-Api -Method Post -Uri "$API_BASE/projects" -Body @{
        slug        = $PROJECT_SLUG
        name        = "Smoke Stub Test $TIMESTAMP"
        repo_path   = "F:\dev\agentrouter"
        memory_path = ".ai_memory/projects/$PROJECT_SLUG"
        default_branch = "main"
        status      = "active"
        stack       = @{ framework = "fastapi" }
    } -TimeoutSec 30
    $projectId = $project.id
    Write-Host "[INFO] Project created: $projectId"
} catch {
    $errMsg = $_.Exception.Message
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $errMsg = $reader.ReadToEnd()
    }
    Exit-Fail "Failed to create project: $errMsg"
}

# ── create agent ────────────────────────────────────────────────────────
Write-Host "[INFO] Creating agent '$AGENT_SLUG' ..."
try {
    $agent = Invoke-Api -Method Post -Uri "$API_BASE/agents" -Body @{
        slug          = $AGENT_SLUG
        name          = "Smoke Agent $TIMESTAMP"
        role          = "smoke_tester"
        system_prompt = "You are a smoke test agent. Plan only."
        model         = "stub"
        permissions   = @{ read_files = $true; write_files = $false }
        status        = "active"
    } -TimeoutSec 30
    $agentId = $agent.id
    Write-Host "[INFO] Agent created: $agentId"
} catch {
    $errMsg = $_.Exception.Message
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $errMsg = $reader.ReadToEnd()
    }
    Exit-Fail "Failed to create agent: $errMsg"
}

# ── create task ─────────────────────────────────────────────────────────
Write-Host "[INFO] Creating task..."
try {
    $task = Invoke-Api -Method Post -Uri "$API_BASE/tasks" -Body @{
        title           = "Smoke stub test task"
        raw_text        = "Verify that the stub runtime correctly generates a plan."
        normalized_text = "Verify stub runtime plan generation"
        risk_level      = "low"
        intent          = "smoke_test"
        project_id      = $projectId
        agent_id        = $agentId
    } -TimeoutSec 30
    $taskId = $task.id
    Write-Host "[INFO] Task created: $taskId (status: $($task.status))"
} catch {
    $errMsg = $_.Exception.Message
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $errMsg = $reader.ReadToEnd()
    }
    Exit-Fail "Failed to create task: $errMsg"
}

# ── set task to routed so runtime can accept it ─────────────────────────
Write-Host "[INFO] Routing task to planning..."
try {
    $routedTask = Invoke-Api -Method Patch -Uri "$API_BASE/tasks/$taskId/status" -Body @{
        status = "routed"
    } -TimeoutSec 30
    $routedTask = Invoke-Api -Method Patch -Uri "$API_BASE/tasks/$taskId/status" -Body @{
        status = "planning"
    } -TimeoutSec 30
    Write-Host "[INFO] Task status set to: $($routedTask.status)"
} catch {
    # May already be in valid state; proceed
    Write-Host "[INFO] Task status transition: attempting plan directly"
}

# ── call plan endpoint ──────────────────────────────────────────────────
Write-Host ""
Write-Host "**************************************************"
Write-Host "* Worker bypass: direct POST /runtime used.      *"
Write-Host "**************************************************"
Write-Host ""

Write-Host "[INFO] Calling POST /runtime/tasks/$taskId/plan (timeout 120s)..."
$planRequestStart = Get-Date
try {
    $planResult = Invoke-Api -Method Post -Uri "$API_BASE/runtime/tasks/$taskId/plan" -TimeoutSec 120
    $planDuration = ((Get-Date) - $planRequestStart).TotalSeconds
} catch {
    $errMsg = $_.Exception.Message
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $errMsg = $reader.ReadToEnd()
    }
    Exit-Fail "Plan generation failed: $errMsg"
}

# ── fetch task details for verification ─────────────────────────────────
Write-Host "[INFO] Fetching updated task..."
try {
    $updatedTask = Invoke-Api -Method Get -Uri "$API_BASE/tasks/$taskId" -TimeoutSec 30
} catch {
    Exit-Fail "Failed to fetch updated task."
}

# ── fetch task events ───────────────────────────────────────────────────
Write-Host "[INFO] Fetching task events..."
try {
    $events = Invoke-Api -Method Get -Uri "$API_BASE/task-events?task_id=$taskId" -TimeoutSec 30
    if ($events -is [array]) {
        $eventList = $events
    } elseif ($events.PSObject.Properties.Name -contains "items") {
        $eventList = $events.items
    } elseif ($events.PSObject.Properties.Name -contains "events") {
        $eventList = $events.events
    } else {
        $eventList = @($events)
    }
} catch {
    Write-Host "[WARN] Could not fetch task events: $_"
    $eventList = @()
}

# ── verifications ───────────────────────────────────────────────────────
$checks = @{
    status_approved          = $false
    session_id_stub          = $false
    plan_generated_count     = 0
    runtime_error            = 0
    policy_blocked           = 0
    command_started          = 0
    command_finished         = 0
    file_changed             = 0
    sandbox_created          = 0
}

# Check status
$checks.status_approved = ($updatedTask.status -eq "approved")

# Check session_id in payload
$payload = if ($updatedTask.payload) { $updatedTask.payload } else { @{} }
if ($payload -is [string]) { $payload = $payload | ConvertFrom-Json }
$runtimePlan = $payload.runtime_plan
if ($runtimePlan) {
    $sessionId = $runtimePlan.session_id
    if ($sessionId -eq "stub-session") {
        $checks.session_id_stub = $true
    }
}

# Analyze events
foreach ($evt in $eventList) {
    $evtType = $evt.event_type
    if ($evtType -eq "plan_generated") { $checks.plan_generated_count++ }
    if ($evtType -eq "runtime_error") { $checks.runtime_error++ }
    if ($evtType -eq "policy_blocked") { $checks.policy_blocked++ }
    if ($evtType -eq "command_started") { $checks.command_started++ }
    if ($evtType -eq "command_finished") { $checks.command_finished++ }
    if ($evtType -eq "file_changed") { $checks.file_changed++ }
    if ($evtType -eq "sandbox" -or $evtType -eq "sandbox_created") { $checks.sandbox_created++ }
}

$checks.plan_generated_count = [int]$checks.plan_generated_count

# Check git still clean
$gitStatusAfter = git status --porcelain 2>&1
$gitStillClean = (-not $gitStatusAfter)

# ── report ──────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========== Smoke Stub Runtime Report =========="
Write-Host "  Task ID            : $taskId"
Write-Host "  Project slug       : $PROJECT_SLUG"
Write-Host "  Agent slug         : $AGENT_SLUG"
Write-Host "  Plan duration      : $([math]::Round($planDuration, 1))s"
Write-Host ""
Write-Host "  status=approved    : $(if ($checks.status_approved) { '[PASS]' } else { '[FAIL]' })"
Write-Host "  session_id=stub    : $(if ($checks.session_id_stub) { '[PASS]' } else { '[FAIL]' })"
Write-Host "  plan_generated=1   : $(if ($checks.plan_generated_count -eq 1) { '[PASS]' } else { '[FAIL] (got: $($checks.plan_generated_count))' })"
Write-Host "  no runtime_error   : $(if ($checks.runtime_error -eq 0) { '[PASS]' } else { '[FAIL] ($($checks.runtime_error))' })"
Write-Host "  no policy_blocked  : $(if ($checks.policy_blocked -eq 0) { '[PASS]' } else { '[FAIL] ($($checks.policy_blocked))' })"
Write-Host "  no command/file    : $(if ($checks.command_started -eq 0 -and $checks.file_changed -eq 0) { '[PASS]' } else { '[FAIL]' })"
Write-Host "  no sandbox events  : $(if ($checks.sandbox_created -eq 0) { '[PASS]' } else { '[FAIL]' })"
Write-Host "  git still clean    : $(if ($gitStillClean) { '[PASS]' } else { '[FAIL]' })"
Write-Host "================================================="
Write-Host ""

# Determine overall result
$allPassed = ($checks.status_approved -and
              $checks.session_id_stub -and
              $checks.plan_generated_count -eq 1 -and
              $checks.runtime_error -eq 0 -and
              $checks.policy_blocked -eq 0 -and
              $checks.command_started -eq 0 -and
              $checks.file_changed -eq 0 -and
              $checks.sandbox_created -eq 0 -and
              $gitStillClean)

if ($allPassed) {
    Write-Host "[PASS] All smoke checks passed for stub runtime."
    exit 0
} else {
    Write-Host "[FAIL] Some checks failed. Review report above."
    exit 1
}
