# Local Runner Protocol Draft (DEV-12A)

## Scope

Design-only protocol for future Local Runner integration. No implementation in DEV-12A.

## Core entities

- **Runner** — logical runner identity registered in cloud
- **RunnerDevice** — physical host/device metadata
- **RunnerSession** — active pairing/auth session
- **WorkspaceSource** — selected source mode (`local_runner`, `cloud_workspace`, `github_repository`)
- **ProjectFolder** — discovered project path inside allowed root
- **FileOperationRequest** — read/search/patch proposal request
- **RunnerJob** — cloud-assigned work item for runner
- **RunnerJobResult** — completed runner job result
- **RunnerCapability** — declared capability flags
- **RunnerHeartbeat** — periodic liveness/status payload
- **RunnerApprovalLink** — relation to approval item
- **AuditEvent** — append-only security event

## Runner states

- `not_connected`
- `pairing`
- `online`
- `offline`
- `suspended`
- `revoked`
- `error`

## Workspace states

- `no_workspace`
- `runner_connected`
- `project_selected`
- `read_only`
- `write_pending_approval`
- `execution_disabled`
- `error`

## Transport options

### Compared options
1. Runner polls cloud API
2. WebSocket (runner → cloud)
3. SSE
4. Local HTTP server
5. Reverse tunnel

### MVP recommendation

Use **outbound-only** connectivity from runner to cloud:

- Polling or WebSocket from runner to cloud
- No inbound port on user machine
- Cloud never directly connects to user LAN
- Better NAT/firewall compatibility and safer boundary

## Required protocol operations

### Pairing
- `runner.start_pairing`
- `runner.register`
- `runner.verify_pairing_code`
- `runner.revoke`

### Heartbeat
- `runner.heartbeat`
- `runner.status`

### Discovery
- `runner.list_projects`
- `runner.list_tree`
- `runner.stat_path`

### Read
- `runner.read_file`
- `runner.search_files`
- `runner.get_file_snippet`

### Write planning
- `runner.propose_patch`
- `runner.preview_diff`

### Approved write
- `runner.apply_patch`
- `runner.create_file`
- `runner.rename_file`
- `runner.delete_file`

### Command planning
- `runner.propose_command`
- `runner.explain_command`

### Approved command (future only)
- `runner.run_command`
- **Status in DEV-12A:** FUTURE, approval-gated, disabled by default

## RunnerJob result model

- `job_id`
- `status`
- `started_at`
- `finished_at`
- `stdout` (redacted)
- `stderr` (redacted)
- `files_changed`
- `diff_summary`
- `safety_flags`
- `approval_id`

## Notes

- Protocol is intentionally approval-centric.
- Any write/command operation must be auditable and linked to explicit safety class.
