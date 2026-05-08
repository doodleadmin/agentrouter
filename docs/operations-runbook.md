# Operations Runbook — Agent Mission Control

Version: 1.0
Audience: DevOps / On-call Administrator

## Service Management (systemd)

### Start all services

```bash
sudo systemctl start agentrouter-api
sudo systemctl start agentrouter-worker
sudo systemctl start agentrouter-telegram-bot
```

### Stop all services

```bash
sudo systemctl stop agentrouter-telegram-bot
sudo systemctl stop agentrouter-worker
sudo systemctl stop agentrouter-api
```

### Restart a single service

```bash
sudo systemctl restart agentrouter-api
sudo systemctl restart agentrouter-worker
sudo systemctl restart agentrouter-telegram-bot
```

### Enable/disable on boot

```bash
sudo systemctl enable agentrouter-api agentrouter-worker agentrouter-telegram-bot
sudo systemctl disable agentrouter-api agentrouter-worker agentrouter-telegram-bot
```

## Safe Restart Order

Always restart in dependency order to avoid cascading failures:

```
Stop:   bot → worker → api → (keep postgres/redis running)
Start:  api → worker → bot
```

```bash
# Full safe restart
sudo systemctl stop agentrouter-telegram-bot
sudo systemctl stop agentrouter-worker
sudo systemctl restart agentrouter-api
sleep 5
# Verify API is healthy before starting dependents
curl -sf http://127.0.0.1:8000/health || { echo "API not healthy!"; exit 1; }
sudo systemctl start agentrouter-worker
sleep 3
sudo systemctl start agentrouter-telegram-bot
```

## Log Checking

### journalctl — follow live logs

```bash
# API logs
journalctl -u agentrouter-api -f

# Worker logs
journalctl -u agentrouter-worker -f

# Bot logs
journalctl -u agentrouter-telegram-bot -f

# All services at once
journalctl -u agentrouter-api -u agentrouter-worker -u agentrouter-telegram-bot -f
```

### journalctl — recent entries

```bash
# Last 100 lines
journalctl -u agentrouter-api -n 100 --no-pager

# Since yesterday
journalctl -u agentrouter-worker --since yesterday --no-pager

# Errors only
journalctl -u agentrouter-api -p err --no-pager
```

### Docker Compose logs

```bash
docker compose -f infra/docker/docker-compose.prod.yml logs -f api
docker compose -f infra/docker/docker-compose.prod.yml logs -f worker
docker compose -f infra/docker/docker-compose.prod.yml logs -f telegram-bot
docker compose -f infra/docker/docker-compose.prod.yml logs -f --tail=100
```

## Caddy Logs

```bash
# Access logs (JSON format)
sudo tail -f /var/log/caddy/agentrouter-access.log | python -m json.tool

# Caddy journal logs
journalctl -u caddy -f
```

## Health Check Monitoring

### Manual health checks

```bash
# API health — expect {"status":"ok","version":"0.1.0"}
curl -sf http://127.0.0.1:8000/health | python -m json.tool

# API version
curl -sf http://127.0.0.1:8000/version | python -m json.tool

# PostgreSQL connectivity
pg_isready -U agentmc -d agentrouter

# Redis connectivity
redis-cli ping
# Expect: PONG
```

### Continuous monitoring (one-liner)

```bash
# Check every 10 seconds
watch -n 10 'curl -sf http://127.0.0.1:8000/health 2>&1 || echo "API DOWN"'
```

## Service Status

```bash
# Quick status of all services
systemctl is-active agentrouter-api agentrouter-worker agentrouter-telegram-bot

# Detailed status
systemctl status agentrouter-api
systemctl status agentrouter-worker
systemctl status agentrouter-telegram-bot

# Docker Compose status
docker compose -f infra/docker/docker-compose.prod.yml ps
```

## Database Operations

### Backup (before migrations or risky changes)

```bash
# Create backup
pg_dump -U agentmc -d agentrouter -F c -f /opt/agent-control/backups/agentrouter_$(date +%Y%m%d_%H%M%S).dump

# List backups
ls -la /opt/agent-control/backups/
```

### Restore from backup

```bash
# Stop services that use DB
sudo systemctl stop agentrouter-telegram-bot agentrouter-worker agentrouter-api

# Restore
pg_restore -U agentmc -d agentrouter -c /opt/agent-control/backups/agentrouter_YYYYMMDD_HHMMSS.dump

# Restart
sudo systemctl start agentrouter-api
sleep 5
sudo systemctl start agentrouter-worker
sudo systemctl start agentrouter-telegram-bot
```

### Run migrations

```bash
# Check current migration state
cd /opt/agent-control/agentrouter/apps/api
sudo -u agentmc .venv/bin/alembic current

# Apply pending migrations
sudo -u agentmc .venv/bin/alembic upgrade head

# Downgrade one step (rollback)
sudo -u agentmc .venv/bin/alembic downgrade -1
```

## Common Troubleshooting

### API won't start

```bash
# Check logs
journalctl -u agentrouter-api -n 50 --no-pager

# Common causes:
# - DATABASE_URL incorrect or DB unreachable
# - Port 8000 already in use: sudo lsof -i :8000
# - .env file missing or wrong permissions: ls -la /opt/agent-control/agentrouter/.env
```

### Worker not processing tasks

```bash
# Check worker logs
journalctl -u agentrouter-worker -n 50 --no-pager

# Verify Redis connectivity
redis-cli ping

# Check Celery inspect
cd /opt/agent-control/agentrouter/apps/worker
sudo -u agentmc .venv/bin/celery -A app.celery_app inspect active
sudo -u agentmc .venv/bin/celery -A app.celery_app inspect reserved
```

### Bot not responding

```bash
# Check bot logs
journalctl -u agentrouter-telegram-bot -n 50 --no-pager

# Verify API is reachable from bot's perspective
curl -sf http://127.0.0.1:8000/health

# Check token key is set (do not print value)
grep -q '^TELEGRAM_BOT_TOKEN=' /opt/agent-control/agentrouter/.env && echo "TELEGRAM_BOT_TOKEN: set" || echo "TELEGRAM_BOT_TOKEN: missing"

# Ensure only ONE bot instance is running
ps aux | grep 'app.main' | grep telegram
```

## What NOT to Do

### Never in production

| Action | Why |
|--------|-----|
| `SQL_ECHO=true` | Logs SQLAlchemy bind params which may contain user text |
| `DEBUG=true` | Enables debug mode with verbose error details |
| Put secrets in `.service` files | systemd units may be world-readable |
| Bind API to `0.0.0.0` | Exposes API directly to internet, bypassing Caddy |
| Run multiple bot instances | Causes duplicate Telegram message processing |

## Scripted release/rollback operations

Use guarded scripts for reproducible operator actions:

```bash
DRY_RUN=true ENV_FILE=.env.example PROJECT_ROOT="$PWD" scripts/deploy/preflight.sh
DRY_RUN=true RELEASE_COMMIT="$(git rev-parse HEAD)" scripts/deploy/release.sh
DRY_RUN=true ROLLBACK_COMMIT="$(git rev-parse HEAD)" scripts/deploy/rollback.sh
DRY_RUN=true HEALTH_URL=http://127.0.0.1:8000/health scripts/deploy/smoke.sh
```

Notes:
- scripts are **safe by default** (`DRY_RUN=true` unless overridden);
- live deploy and live rollback are intentionally blocked inside scripts and must be performed only through approved CI/CD or manual approved runbook.
| Deploy directly to `main` branch | Must go through PR + approval workflow |
| `rm -rf` outside project directory | Destructive and irreversible |
| Force push to `main` | Destroys history and audit trail |
| Share `.env` in chat/email | Use a secrets manager or encrypted channel |
| Run agents outside Docker sandbox | Uncontrolled code execution on host |

### Verification checklist after any config change

```bash
# 1. No DEBUG or SQL_ECHO enabled
grep -r 'DEBUG=true\|SQL_ECHO=true' /opt/agent-control/agentrouter/.env
# Should return nothing

# 2. API only on localhost
grep 'host' /etc/systemd/system/agentrouter-api.service
# Should show 127.0.0.1, NOT 0.0.0.0

# 3. .env permissions
ls -la /opt/agent-control/agentrouter/.env
# Should show -rw------- (600) owned by agentmc

# 4. Only one bot process
ps aux | grep 'telegram-bot.*app.main' | grep -v grep
# Should show exactly one process
```
