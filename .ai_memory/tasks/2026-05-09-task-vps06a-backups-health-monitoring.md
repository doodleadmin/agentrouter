# 2026-05-09 — VPS-06A: Backups + Health Monitoring Baseline

- **Agent:** studio-orchestrator
- **Scope:** VPS 45.130.213.12, systemd timer setup, no app restart, no migrations, no OpenCode
- **Gate:** CONFIRM_VPS06A_OPS=yes

## What was done

### Backup script
- Created `/usr/local/sbin/agentrouter-db-backup.sh` (root:root, 750)
- Sources `.env` without printing values
- Uses `docker compose exec -T postgres pg_dump` for safe container-level backup
- Retention: 14 days (auto-delete via `find -mtime`)
- Backups stored in `/var/lib/agentrouter/backups/` (mode 600)

### Backup systemd timer
- Service: `agentrouter-db-backup.service` (Type=oneshot)
- Timer: `agentrouter-db-backup.timer` (daily at 03:20 UTC, randomized 15min delay)
- Enabled and started ✅

### Healthcheck script
- Created `/usr/local/sbin/agentrouter-healthcheck.sh` (root:root, 750)
- Checks: local API (`127.0.0.1:8000/health`), HTTPS API (`polyrouter.ru/health`), PostgreSQL (`pg_isready`), Redis (`redis-cli ping`)
- Appends one-line compact log entry to `/var/log/agentrouter/healthcheck.log` (mode 640)
- No secrets printed

### Healthcheck systemd timer
- Service: `agentrouter-healthcheck.service` (Type=oneshot)
- Timer: `agentrouter-healthcheck.timer` (every 5 minutes, OnBootSec=2m)
- Enabled and started ✅

### Manual verification
- Manual backup: `agentrouter-20260509-190435.sql` — **19677 bytes** ✅
- Manual healthcheck: `local=OK https=OK postgres=OK redis=OK` ✅

## Runtime state maintained
- All 5 containers healthy (api, postgres, redis, worker, telegram-bot)
- HTTPS `/health` OK
- Caddy active, UFW 22/80/443 unchanged
- App NOT restarted — uptime ~1h for api/worker/bot, ~12h for postgres/redis
- Migrations NOT run
- OpenCode NOT started

## What was NOT done
- ❌ App containers NOT restarted
- ❌ Migrations NOT run
- ❌ OpenCode NOT started
- ❌ No secrets printed
- ❌ No code/deploy script changes
- ❌ No git push
- ❌ No Caddy config changes
- ❌ No firewall changes

## Risks / Warnings
| Risk | Severity | Detail |
|------|----------|--------|
| Backup script sources `.env` with `set -a` | ⚠️ Low | All env vars in shell memory during script run. Script runs as root (isolated systemd). No echo of values. |
| No off-server backup | ⚠️ Medium | Backups are on same disk. Recommend adding `scp` or S3 sync in VPS-06B. |
| Healthcheck log rotation not configured | ⚠️ Low | File at ~100 bytes per check × 288/day × 14 days ≈ 400KB — manageable. Add logrotate later. |

## Next step
**VPS-06B:** Log retention / off-server backup / alerting / uptime monitoring
