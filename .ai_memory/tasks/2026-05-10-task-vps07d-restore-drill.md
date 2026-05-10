# VPS-07D — Offsite Backup Restore Drill

Date: 2026-05-10  
Agent: studio-orchestrator  
Target: VPS `45.130.213.12` (`agentmc`, `root`)  
Status: **completed after path alignment (safe execution, no production impact)**

## Scope and safety gates
- Confirmation received: `CONFIRM_VPS07D_RESTORE_DRILL=yes`
- Forbidden actions respected:
  - no production DB restore
  - no app container restarts
  - no Docker daemon restart
  - no migrations
  - no OpenCode start
  - no secrets output

## Baseline checks
- Local git: clean, `main...origin/main`, latest local commit includes VPS-07C memory.
- VPS runtime baseline: PASS
  - compose prod: all 5 containers healthy
  - HTTPS health: PASS
  - timers active: 4 (`healthcheck`, `db-backup`, `backup-verify`, `offsite-sync`)
  - UFW unchanged: 22/80/443

## Restore drill implementation
- Restore drill script installed: `/usr/local/sbin/agentrouter-restore-drill.sh`
  - ownership/mode: `root:root 750`
  - syntax check: PASS
- Script behavior includes:
  - source backup from S3
  - header/footer verification (`PostgreSQL database dump` + `... dump complete`)
  - optional local-vs-S3 sha256 match check
  - isolated temporary PostgreSQL container (`--network none`, no published ports)
  - restore into temporary DB only
  - verification by table count + alembic version only
  - cleanup trap for temp container and temp directory

## Run result
- Manual execution result: **`RESTORE_DRILL_FAIL rclone_target_env_missing`**
- Failure reason is sanitized (no secrets).
- Because required rclone target env file was missing, drill did not proceed to S3 download in this run.

## Retry run (VPS-07D retry)
- Confirmation received: `CONFIRM_VPS07D_RETRY=yes`
- Root cause remediation applied:
  - recreated `/root/.config/rclone/agentrouter-s3-target.env`
  - non-secret metadata only (`S3_REMOTE_NAME`, `S3_PROVIDER`, `S3_ENDPOINT`, `S3_BUCKET`, `S3_REGION`)
  - permissions: `root:root 600`
- rclone checks:
  - `rclone` installed and remote `agentrouter-s3` exists
  - `rclone.conf` permissions verified: `root:root 600`
- S3 listing result (filenames only): backups exist in bucket root.
- Retry execution result: **`RESTORE_DRILL_FAIL backup_not_found_in_s3 agentrouter-20260510-050111.sql`**
- Sanitized interpretation: restore script expects object under `.../agentrouter/backups/`, but backup files are currently at bucket root path.

## VPS-07D.1 Path Alignment + Final Retry
- Confirmation received: `CONFIRM_VPS07D1_PATH_ALIGN=yes`
- Canonical S3 path selected: `agentrouter/backups/`.
- Safe S3 inspection (filenames only):
  - root path had: `agentrouter-20260509-190435.sql`, `agentrouter-20260510-033455.sql`, `agentrouter-20260510-050111.sql`
  - canonical path initially empty
- Path alignment action (copy-only, no delete):
  - copied `agentrouter-*.sql` from bucket root to `agentrouter/backups/`
  - root-level backups were **not deleted**
- Offsite sync script alignment:
  - updated `/usr/local/sbin/agentrouter-offsite-sync.sh` to use remote path `agentrouter/backups`
  - backup of previous script created
  - syntax check PASS, permissions `root:root 750`
- Manual offsite sync result: `OFFSITE_SYNC_OK latest=agentrouter-20260510-050111.sql remote_path=agentrouter/backups`
- Canonical listing after alignment/sync: contains `agentrouter-*.sql` files.
- Final restore drill result: **`RESTORE_DRILL_OK backup=agentrouter-20260510-050111.sql source=s3 size=19677 table_count=10 alembic_version=0002_add_security_audit_events`**
- Restore used isolated temporary PostgreSQL container (`--network none`, no published ports).
- Cleanup PASS: no temporary restore-drill container/dir remained.

## Cleanup and post-checks
- Temporary restore-drill containers: none remaining (PASS)
- Temporary restore-drill directories: none remaining (PASS)
- Restore-drill log tail includes prior successful entry metadata only (no secrets):
  - `backup=agentrouter-20260510-050111.sql`
  - `source=s3`
  - `size=19677`
  - `table_count=10`
  - `alembic_version=0002_add_security_audit_events`
- Final runtime verify: PASS
  - all prod containers still healthy
  - HTTPS health OK
  - 4 timers active
  - UFW unchanged

## Compliance checklist
- restore drill script installed: ✅
- source backup came from S3: ✅ (canonical path)
- backup filename and size only: ✅ (`agentrouter-20260510-050111.sql`, `19677` bytes)
- header/footer verification PASS: ✅
- sha256 local-vs-S3 match PASS if available: ✅
- temporary isolated PostgreSQL container used: ✅
- no published ports: ✅ (script design)
- production DB not touched: ✅
- restore PASS: ✅
- table count only, no row data: ✅
- alembic version if shown: ✅
- temporary container cleaned up: ✅
- temporary files cleaned up: ✅
- final runtime still healthy: ✅
- all 4 timers still active: ✅
- app containers not restarted: ✅
- Docker daemon not restarted: ✅
- Caddy config unchanged: ✅
- UFW unchanged: ✅
- migrations not run: ✅
- OpenCode not started: ✅
- secrets not displayed: ✅

## Next step
- VPS-07E recommended:
  1) implement Docker log rotation limits for container logs, or
  2) proceed with controlled OpenCode activation workflow (if in current scope).

## Memory checkpoint
- **Memory updated:** yes
- **Files updated:**
  - `PROJECT_MEMORY.md`
  - `.ai_memory/current_state.md`
  - `.ai_memory/_INDEX.md`
  - `.ai_memory/tasks/2026-05-10-task-vps07d-restore-drill.md`
- **Commit hash:** not committed (as requested)
