# 2026-05-09 — VPS-06C: Offsite Backup Sync to Beget S3 (VPS 45.130.213.12)

- **Agent:** studio-orchestrator
- **Scope:** VPS 45.130.213.12, rclone S3 sync + systemd timer, no app restart, no migrations
- **Domain:** polyrouter.ru
- **S3 Provider:** Beget Object Storage (s3.ru1.storage.beget.cloud)
- **Bucket:** e680fb27b2d5-polyrouter
- **Safety constraints:** no .env print, no secret values output, no app container restart, no Docker daemon restart, no Caddy config change, no UFW change, no migrations, no OpenCode

## S3 Credential Issue

Initial rclone config failed with `SignatureDoesNotMatch 403` because access key and secret key were identical (`1TG16UT19BN9TCEIT4X8`). Cross-verified with s3cmd — same error. After user provided correct secret key (different from access key), rclone immediately authenticated and listed the bucket.

## Actions Executed

1. Verified runtime baseline: all 5 containers healthy, HTTPS health OK, 3 timers active
2. Installed `s3cmd` for cross-verification (confirmed consistent error across tools)
3. Installed `rclone` from Ubuntu apt (v1.60.1-DEV)
4. Configured rclone S3 remote at `/root/.config/rclone/rclone.conf` (root:root, 600)
   - Endpoint: `https://s3.ru1.storage.beget.cloud`
   - `force_path_style = true`, `no_check_bucket = true`, `no_head_bucket = true`
5. Verified rclone auth + read/write: `rclone lsd` listed bucket, `rclone rcat` uploaded marker
6. Created offsite sync script: `/usr/local/sbin/agentrouter-offsite-sync.sh` (root:root, 750)
   - Syncs `/var/lib/agentrouter/backups/*.sql` → `agentrouter-s3:e680fb27b2d5-polyrouter/`
   - Timestamped logging to `/var/log/agentrouter/offsite-sync.log`
   - Log rotation: keeps last 500 lines
   - Uses `rclone sync` (copy new, skip existing, no delete)
7. Created systemd service + timer:
   - `agentrouter-offsite-sync.service` (oneshot, root, Nice=10, idle IO)
   - `agentrouter-offsite-sync.timer` (daily at 05:00 UTC, 10min random delay, persistent)
8. Ran manual offsite sync: `agentrouter-20260509-190435.sql` (19677 bytes) synced successfully
9. Final runtime: all 5 containers healthy, HTTPS OK, UFW unchanged

## Key Evidence

- Bucket listed: `e680fb27b2d5-polyrouter` (size -1, date 2026-05-09 20:17:23)
- Write test: `marker.txt` (20 bytes) uploaded to S3
- Manual sync: `SYNC_OK exit=0` for `agentrouter-20260509-190435.sql` (19677 bytes, 0.4s)
- Bucket contents after sync: `agentrouter-20260509-190435.sql` (19677) + `marker.txt` (20)
- All 4 timers active:
  - `agentrouter-healthcheck.timer` — every 5min
  - `agentrouter-db-backup.timer` — daily 03:20 UTC
  - `agentrouter-backup-verify.timer` — daily 04:00 UTC
  - `agentrouter-offsite-sync.timer` — daily 05:00 UTC
- App containers uptime: api/worker/bot ~5h, postgres/redis ~15h

## What Was NOT Done

- ❌ App containers NOT restarted
- ❌ Docker daemon NOT restarted
- ❌ Caddy config NOT changed
- ❌ UFW NOT changed (22/80/443)
- ❌ Migrations NOT run
- ❌ OpenCode NOT started
- ❌ Secrets NOT printed

## Warnings / Deferred Items

| Item | Severity | Note |
|------|----------|------|
| S3 credentials on VPS | ⚠️ Low | Access + secret keys in `/root/.config/rclone/rclone.conf` (root:root, 600) — required for automated sync |
| Bucket management via panel only | ⚠️ Low | Beget S3 does not support bucket creation/del via S3 API — managed via Beget control panel |
| No sync alerts | ⚠️ Low | If offsite sync fails, only detected via log review — consider alerting in future |

## Next Step

**VPS-07:** External uptime monitoring + alerting baseline (e.g., UptimeRobot/Healthchecks.io on `https://polyrouter.ru/health`).

## Memory Checkpoint

- **Memory updated:** yes
- **Files updated:** PROJECT_MEMORY.md, .ai_memory/current_state.md, .ai_memory/_INDEX.md
- **Commit:** pending (commit message: `docs(vps): record offsite s3 backup sync`)
- **Skipped reason:** n/a
