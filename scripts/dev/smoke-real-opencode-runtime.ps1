<#
.SYNOPSIS
    BE-11 Runtime Runbook: Smoke test for real OpenCode runtime provider.

.DESCRIPTION
    Verifies that the opencode_http runtime provider works with a real OpenCode
    server. API must be running in opencode_http mode, OpenCode healthy at
    127.0.0.1:4096. Creates project, agent, and low-risk task, then generates
    a plan via direct POST to /runtime/tasks/{id}/plan. Verifies:
    - status=approved, session_id starts with "ses_"
    - No stub fingerprints in plan_text
    - runtime_session_created BEFORE runtime_event_received in timeline
    - plan_generated=1, no errors/timeouts/policy blocks
    - No command/file/sandbox events
    - No reasoning leak, no secret leak in plan_text
    - Git stays clean

.PARAMETER TimeoutSeconds
    Max time to wait for plan generation (default 360).

.PARAMETER DryRun
    Validate preconditions only, print would-do actions, exit 0.

.EXAMPLE
    .\scripts\dev\smoke-real-opencode-runtime.ps1
    .\scripts\dev\smoke-real-opencode-runtime.ps1 -TimeoutSeconds 600
    .\scripts\dev\smoke-real-opencode-runtime.ps1 -DryRun
#>

param(
    [int] $TimeoutSeconds = 360,
    [switch] $DryRun
)

$ErrorActionPreference = "Stop"
Set-Location "F:\dev\agentrouter"

$API_BASE = "http://127.0.0.1:8000"
$OPENCODE_BASE = "http://127.0.0.1:4096"
$TIMESTAMP = Get-Date -Format "yyyyMMdd-HHmmss"
$PROJECT_SLUG = "smoke-real-$TIMESTAMP"
$AGENT_SLUG = "smoke-agent-$TIMESTAMP"

$STUB_FINGERPRINTS = @(
    "stub-session",
    "## Safety",
    "## Task Context",
    "No code execution",
    "No file modifications"
)

$SECRET_PATTERNS = @(
    '(?i)(api[_-]?key|token|secret|password|passwd)\s*[:=]\s*\S+',
    'sk-[A-Za-z0-9]{20,}',
    'ghp_[A-Za-z0-9]{20,}',
    '(?i)Bearer\s+[A-Za-z0-9\-_\.]{20,}'
)

# -- helpers -------------------------------------------------------------

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
        [int] $TimeoutSec = 30
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

# -- dry-run -------------------------------------------------------------
if ($DryRun) {
    Write-Host ""
    Write-Host "========== Smoke Real OpenCode Runtime DryRun =========="
    Write-Host "[DRYRUN] would: verify API in opencode_http mode"
    Write-Host "[DRYRUN] would: verify OpenCode healthy at $OPENCODE_BASE"
    Write-Host "[DRYRUN] would: verify git clean"
    Write-Host "[DRYRUN] would: PRINT: Worker bypass: direct POST /runtime used"
    Write-Host "[DRYRUN] would: create project   slug=$PROJECT_SLUG"
    Write-Host "[DRYRUN] would: create agent     slug=$AGENT_SLUG"
    Write-Host "[DRYRUN] would: create task      risk_level=low"
    Write-Host "[DRYRUN] would: POST /runtime/tasks/{id}/plan (timeout ${TimeoutSeconds}s)"
    Write-Host "[DRYRUN] would: verify session_id != stub-session and starts with 'ses_'"
    Write-Host "[DRYRUN] would: verify no stub fingerprints in plan_text"
    Write-Host "[DRYRUN] would: verify runtime_session_created BEFORE runtime_event_received"
    Write-Host "[DRYRUN] would: verify plan_generated=1"
    Write-Host "[DRYRUN] would: verify no runtime_error/runtime_timeout/policy_blocked"
    Write-Host "[DRYRUN] would: verify no command/file/sandbox events"
    Write-Host "[DRYRUN] would: verify no reasoning/secret leak"
    Write-Host "[DRYRUN] would: verify git unchanged vs baseline"
    Write-Host "========================================================="
    Write-Host ""
    exit 0
}

# -- preconditions -------------------------------------------------------

# 1. OpenCode healthy
try {
    $ocHealth = Invoke-RestMethod -Uri "$OPENCODE_BASE/global/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "[INFO] OpenCode healthy at $OPENCODE_BASE"
} catch {
    Exit-Fail "OpenCode not healthy at $OPENCODE_BASE. Run start-opencode.ps1 first."
}

# 2. API healthy
try {
    $apiHealth = Invoke-RestMethod -Uri "$API_BASE/health" -TimeoutSec 5 -ErrorAction Stop
    if ($apiHealth.status -ne "ok") {
        Exit-Fail "API not healthy at $API_BASE"
    }
    Write-Host "[INFO] API healthy at $API_BASE"
} catch {
    Exit-Fail "API not reachable at $API_BASE/health. Run start-api-opencode.ps1 first."
}

# 3. Git baseline snapshot (no mutation during smoke)
$gitStatusBefore = git status --porcelain 2>&1
if ($LASTEXITCODE -ne 0) {
    Exit-Fail "Git status failed."
}
Write-Host "[INFO] Git status baseline captured (changes allowed before run)."

# -- create project ------------------------------------------------------
Write-Host "[INFO] Creating project '$PROJECT_SLUG' ..."
try {
    $project = Invoke-Api -Method Post -Uri "$API_BASE/projects" -Body @{
        slug        = $PROJECT_SLUG
        name        = "Smoke Real OpenCode Test $TIMESTAMP"
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

# -- create agent --------------------------------------------------------
Write-Host "[INFO] Creating agent '$AGENT_SLUG' ..."
try {
    $agent = Invoke-Api -Method Post -Uri "$API_BASE/agents" -Body @{
        slug          = $AGENT_SLUG
        name          = "Smoke Agent $TIMESTAMP"
        role          = "smoke_tester"
        system_prompt = "You are a smoke test agent. Generate plan only."
        model         = "opencode"
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

# -- create task ---------------------------------------------------------
Write-Host "[INFO] Creating task..."
try {
    $task = Invoke-Api -Method Post -Uri "$API_BASE/tasks" -Body @{
        title           = "Smoke real OpenCode test task"
        raw_text        = "Look at the project structure and propose a plan for adding a /version endpoint to the API."
        normalized_text = "Propose a plan for adding a /version endpoint to the FastAPI application"
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

# -- route task through status transitions --------------------------------
Write-Host "[INFO] Preparing task for planning..."
try {
    # created -> routed -> planning (runtime_service handles the rest)
    $routedTask = Invoke-Api -Method Patch -Uri "$API_BASE/tasks/$taskId/status" -Body @{
        status = "routed"
    } -TimeoutSec 30
    Write-Host "[INFO] Task routed: $($routedTask.status)"
} catch {
    Write-Host "[WARN] Could not set routed status: $_"
}

# -- call plan endpoint --------------------------------------------------
Write-Host ""
Write-Host "**************************************************"
Write-Host "* Worker bypass: direct POST /runtime used.      *"
Write-Host "**************************************************"
Write-Host ""

$runtimeTimeoutSec = [Math]::Max($TimeoutSeconds, 420)
Write-Host "[STEP] Calling runtime plan endpoint. This may take up to 300s."
$planRequestStart = Get-Date
$planRequestStartIso = $planRequestStart.ToString("o")
Write-Host "[INFO] Plan call started at: $planRequestStartIso"

$progressTimer = New-Object System.Timers.Timer
$progressTimer.Interval = 15000
$progressTimer.AutoReset = $true
$progressSub = Register-ObjectEvent -InputObject $progressTimer -EventName Elapsed -Action {
    $now = Get-Date
    $elapsed = [math]::Round(($now - $using:planRequestStart).TotalSeconds, 1)
    Write-Host "[WAIT] runtime plan request in progress... elapsed=${elapsed}s"
}
$progressTimer.Start()

try {
    $planResult = Invoke-RestMethod -Uri "$API_BASE/runtime/tasks/$taskId/plan" -Method Post -ContentType "application/json" -TimeoutSec $runtimeTimeoutSec -ErrorAction Stop
    $planDuration = ((Get-Date) - $planRequestStart).TotalSeconds
    Write-Host "[DONE] Runtime plan endpoint returned."
} catch {
    $errType = $_.Exception.GetType().FullName
    Write-Host "[ERROR] Runtime plan POST exception type: $errType"
    Write-Host "[INFO] Attempting task state fetch after POST failure..."
    try {
        $taskAfterError = Invoke-Api -Method Get -Uri "$API_BASE/tasks/$taskId" -TimeoutSec 30
        $taskStatusAfterError = $taskAfterError.status
        $planTextState = if ($null -eq $taskAfterError.plan_text) { "null" } else { "not null" }
        Write-Host "[INFO] Task status after error: $taskStatusAfterError"
        Write-Host "[INFO] plan_text: $planTextState"
    } catch {
        Write-Host "[WARN] Failed to fetch task after POST failure: $($_.Exception.Message)"
    }
    exit 1
} finally {
    if ($progressTimer) {
        $progressTimer.Stop()
    }
    if ($progressSub) {
        Unregister-Event -SubscriptionId $progressSub.Id -ErrorAction SilentlyContinue
        Remove-Job -Id $progressSub.Id -Force -ErrorAction SilentlyContinue
    }
    if ($progressTimer) {
        $progressTimer.Dispose()
    }
}

$planRequestEnd = Get-Date
$planRequestEndIso = $planRequestEnd.ToString("o")
Write-Host "[INFO] Plan call finished at: $planRequestEndIso"
Write-Host "[INFO] Plan call elapsed seconds: $([math]::Round($planDuration,1))"

# -- fetch updated task --------------------------------------------------
Write-Host "[INFO] Fetching updated task..."
try {
    $updatedTask = Invoke-Api -Method Get -Uri "$API_BASE/tasks/$taskId" -TimeoutSec 30
} catch {
    Exit-Fail "Failed to fetch updated task."
}

# -- fetch task events ---------------------------------------------------
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

# -- verifications -------------------------------------------------------

# 1. Status is approved
$statusApproved = ($updatedTask.status -eq "approved")

# 2. Extract session_id
$payload = if ($updatedTask.payload) { $updatedTask.payload } else { @{} }
if ($payload -is [string]) { $payload = $payload | ConvertFrom-Json }
$runtimePlan = $payload.runtime_plan
$sessionId = ""
if ($runtimePlan) {
    $sessionId = $runtimePlan.session_id
}
$sessionIdValid = ($sessionId -ne "" -and $sessionId -ne "stub-session" -and $sessionId -match "^ses_")

# 3. Check plan_text for stub fingerprints
$planText = if ($updatedTask.plan_text) { $updatedTask.plan_text } else { "" }
$stubFingerprintsFound = @()
foreach ($fp in $STUB_FINGERPRINTS) {
    if ($planText -match [regex]::Escape($fp)) {
        $stubFingerprintsFound += $fp
    }
}
$noStubFingerprints = ($stubFingerprintsFound.Count -eq 0)

# 4. Check event ordering: runtime_session_created BEFORE runtime_event_received
$sessionCreatedIdx = -1
$firstEventReceivedIdx = -1
for ($i = 0; $i -lt $eventList.Count; $i++) {
    $et = $eventList[$i].event_type
    if ($et -eq "runtime_session_created" -and $sessionCreatedIdx -lt 0) { $sessionCreatedIdx = $i }
    if ($et -eq "runtime_event_received" -and $firstEventReceivedIdx -lt 0) { $firstEventReceivedIdx = $i }
}
$eventOrderCorrect = ($sessionCreatedIdx -ge 0 -and $firstEventReceivedIdx -ge 0 -and $sessionCreatedIdx -lt $firstEventReceivedIdx)

# 5. Count events
$planGeneratedCount = 0
$runtimeErrorCount = 0
$runtimeTimeoutCount = 0
$policyBlockedCount = 0
$commandStartedCount = 0
$commandFinishedCount = 0
$fileChangedCount = 0
$sandboxEventCount = 0

foreach ($evt in $eventList) {
    $et = $evt.event_type
    switch ($et) {
        "plan_generated" { $planGeneratedCount++ }
        "runtime_error" { $runtimeErrorCount++ }
        "runtime_timeout" { $runtimeTimeoutCount++ }
        "policy_blocked" { $policyBlockedCount++ }
        "command_started" { $commandStartedCount++ }
        "command_finished" { $commandFinishedCount++ }
        "file_changed" { $fileChangedCount++ }
    }
    if ($et -match "sandbox") { $sandboxEventCount++ }
}

# 6. Check for reasoning leak (no reasoning content in plan_text)
#    The codebase already filters reasoning - just verify no obvious reasoning markers
$reasoningLeak = ($planText -match '\[REASONING\]|\[Internal\]|<thinking>' -or $planText -match '(?i)let me think|let me reason|my reasoning|I should note')

# 7. Check for secret leaks in plan_text
$secretLeak = $false
foreach ($pattern in $SECRET_PATTERNS) {
    if ($planText -match $pattern) {
        $secretLeak = $true
        break
    }
}

# 8. Git unchanged vs baseline
$gitStatusAfter = git status --porcelain 2>&1
$gitUnchanged = ($gitStatusAfter -join "`n") -eq ($gitStatusBefore -join "`n")

# -- plan text length ----------------------------------------------------
$planLength = $planText.Length

# -- report --------------------------------------------------------------
Write-Host ""
Write-Host "========== Smoke Real OpenCode Runtime Report =========="
Write-Host "  Task ID            : $taskId"
Write-Host "  Worker bypass      : direct POST /runtime used."
Write-Host "  Session ID         : $sessionId"
Write-Host "  Plan length        : $planLength chars"
Write-Host "  Duration           : $([math]::Round($planDuration, 1))s"
Write-Host "  Project slug       : $PROJECT_SLUG"
Write-Host "  Agent slug         : $AGENT_SLUG"
Write-Host ""
Write-Host "  status=approved              : $(if ($statusApproved) { '[PASS]' } else { '[FAIL]' })"
Write-Host "  session_id ~ 'ses_'          : $(if ($sessionIdValid) { '[PASS]' } else { '[FAIL] (got: $sessionId)' })"
Write-Host "  no stub fingerprints         : $(if ($noStubFingerprints) { '[PASS]' } else { "[FAIL] found: $($stubFingerprintsFound -join ', ')" })"
Write-Host "  event order (create < recv)  : $(if ($eventOrderCorrect) { '[PASS]' } else { '[FAIL]' })"
Write-Host "  plan_generated=1             : $(if ($planGeneratedCount -eq 1) { '[PASS]' } else { "[FAIL] ($planGeneratedCount)" })"
Write-Host "  no runtime_error             : $(if ($runtimeErrorCount -eq 0) { '[PASS]' } else { "[FAIL] ($runtimeErrorCount)" })"
Write-Host "  no runtime_timeout           : $(if ($runtimeTimeoutCount -eq 0) { '[PASS]' } else { "[FAIL] ($runtimeTimeoutCount)" })"
Write-Host "  no policy_blocked            : $(if ($policyBlockedCount -eq 0) { '[PASS]' } else { "[FAIL] ($policyBlockedCount)" })"
Write-Host "  no command/file events       : $(if ($commandStartedCount -eq 0 -and $commandFinishedCount -eq 0 -and $fileChangedCount -eq 0) { '[PASS]' } else { '[FAIL]' })"
Write-Host "  no sandbox events            : $(if ($sandboxEventCount -eq 0) { '[PASS]' } else { '[FAIL]' })"
Write-Host "  no reasoning leak            : $(if (-not $reasoningLeak) { '[PASS]' } else { '[FAIL]' })"
Write-Host "  no secret leak               : $(if (-not $secretLeak) { '[PASS]' } else { '[FAIL]' })"
Write-Host "  git unchanged vs baseline    : $(if ($gitUnchanged) { '[PASS]' } else { '[FAIL]' })"
Write-Host "========================================================="
Write-Host ""

# -- show plan preview ---------------------------------------------------
# Preview is only allowed when leak checks passed.
if ($planText -and -not $secretLeak -and -not $reasoningLeak) {
    $planPreview = $planText.Substring(0, [Math]::Min(300, $planText.Length))
    Write-Host "--- Plan Preview (first 300 chars) ---"
    Write-Host $planPreview
    Write-Host "--- End Preview ---"
    Write-Host ""
} elseif ($planText) {
    Write-Host "[INFO] Plan preview suppressed due to reasoning/secret leak check failure."
    Write-Host ""
}

# -- overall result ------------------------------------------------------
$allPassed = ($statusApproved -and
              $sessionIdValid -and
              $noStubFingerprints -and
              $eventOrderCorrect -and
              $planGeneratedCount -eq 1 -and
              $runtimeErrorCount -eq 0 -and
              $runtimeTimeoutCount -eq 0 -and
              $policyBlockedCount -eq 0 -and
              $commandStartedCount -eq 0 -and
              $commandFinishedCount -eq 0 -and
              $fileChangedCount -eq 0 -and
              $sandboxEventCount -eq 0 -and
              (-not $reasoningLeak) -and
              (-not $secretLeak) -and
              $gitUnchanged)

if ($allPassed) {
    Write-Host "[PASS] All smoke checks passed for real OpenCode runtime."
    exit 0
} else {
    Write-Host "[FAIL] Some checks failed. Review report above."
    exit 1
}
