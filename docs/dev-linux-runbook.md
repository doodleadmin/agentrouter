# DEV-LINUX-01: Ubuntu 22.04 Dev Runbook

## Overview

Linux-native development runtime for Agent Mission Control. Replaces Windows PowerShell scripts (`scripts/dev/`) with reliable bash scripts using `nohup` + PID files.

**Target:** WSL2 Ubuntu 22.04 (or any Ubuntu 22.04+ environment)

## Prerequisites

### System Packages

```bash
# Python 3.12+
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Node.js 20+ (for OpenCode CLI)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Docker (for PostgreSQL + Redis)
sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER

# Tools
sudo apt install -y curl jq postgresql-client

# OpenCode CLI
npm install -g opencode
```

### Python Virtual Environment

```bash
cd ~/agentrouter
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e apps/api -e apps/worker -e apps/telegram-bot
```

### Environment

- `.env.local` — copy from `.env.local.example`, fill in `TELEGRAM_BOT_TOKEN` etc.
- All scripts use process-scoped env vars only — never persisted to shell.
- `DATABASE_URL` is only set during `bootstrap-db.sh` and cleaned after.

## Architecture

```
WSL2 Ubuntu 22.04
├── Docker Compose (postgres + redis only)
│   ├── amc-dev-postgres :5432
│   └── amc-dev-redis :6379
├── Native processes (nohup + PID files)
│   ├── API (uvicorn) :8000
│   ├── OpenCode server :4096
│   ├── Celery worker
│   └── Telegram bot
└── Scripts (scripts/dev-linux/)
```

## Quick Start

```bash
# 1. Start Docker services
cd ~/agentrouter
docker compose -f infra/docker/docker-compose.yml up -d

# 2. Check DB
./scripts/dev-linux/check-db.sh

# 3. Bootstrap DB (first time only)
./scripts/dev-linux/bootstrap-db.sh

# 4. Start API (stub mode)
./scripts/dev-linux/start-api-stub.sh

# 5. Start worker
./scripts/dev-linux/start-worker.sh

# 6. Smoke test
./scripts/dev-linux/smoke-stub-runtime.sh
```

## Scripts Reference

### Infrastructure

| Script | Purpose | Port |
|--------|---------|------|
| `check-db.sh` | DB health check (container, tables, alembic) | — |
| `bootstrap-db.sh` | Run alembic migrations | — |

### Services

| Script | Purpose | Port | PID File |
|--------|---------|------|----------|
| `start-api-stub.sh` | API in stub mode | 8000 | `.runtime/api.pid` |
| `start-opencode.sh` | OpenCode server | 4096 | `.runtime/opencode.pid` |
| `start-api-opencode.sh` | API in opencode_http mode | 8000 | `.runtime/api.pid` |
| `start-worker.sh` | Celery worker | — | `.runtime/worker.pid` |
| `start-telegram-bot.sh` | Telegram bot gateway | — | `.runtime/telegram-bot.pid` |

### Smoke Tests

| Script | Purpose | Timeout |
|--------|---------|---------|
| `smoke-stub-runtime.sh` | Stub runtime smoke (plan-only) | 120s |
| `smoke-real-opencode-runtime.sh` | Real OpenCode smoke | 360s |

### Cleanup

| Script | Purpose |
|--------|---------|
| `cleanup-runtime.sh` | Stop all tracked processes, optionally restart API |

## Common Options

All scripts support:

- `--dry-run` — validate preconditions, print would-do actions, exit 0
- `--help` — show usage

## Process Management Pattern

```bash
# Start
nohup python -m uvicorn ... > logs/dev/api.log 2>&1 &
echo $! > .runtime/api.pid

# Check alive
kill -0 $(cat .runtime/api.pid) 2>/dev/null && echo "alive"

# Stop
kill $(cat .runtime/api.pid)
```

## Log Files

All in `logs/dev/`:

- `api-stub.log` — API stub mode output
- `api-opencode.log` — API opencode_http mode output
- `opencode.log` — OpenCode server output
- `worker.log` — Celery worker output
- `telegram-bot.log` — Telegram bot output

## PID Files

All in `.runtime/`:

- `api.pid` — API process
- `opencode.pid` — OpenCode server
- `worker.pid` — Celery worker
- `telegram-bot.pid` — Telegram bot

## Full Runtime: Stub Mode

```bash
docker compose -f infra/docker/docker-compose.yml up -d
./scripts/dev-linux/check-db.sh
./scripts/dev-linux/bootstrap-db.sh
./scripts/dev-linux/start-api-stub.sh
./scripts/dev-linux/start-worker.sh
./scripts/dev-linux/smoke-stub-runtime.sh
# ... work ...
./scripts/dev-linux/cleanup-runtime.sh
```

## Full Runtime: Real OpenCode

```bash
docker compose -f infra/docker/docker-compose.yml up -d
./scripts/dev-linux/check-db.sh
./scripts/dev-linux/start-opencode.sh
./scripts/dev-linux/start-api-opencode.sh
./scripts/dev-linux/start-worker.sh
./scripts/dev-linux/smoke-real-opencode-runtime.sh
# ... work ...
./scripts/dev-linux/cleanup-runtime.sh
```

## Migration from Windows

| Windows (legacy) | Linux (current) |
|------------------|-----------------|
| `scripts/dev/*.ps1` | `scripts/dev-linux/*.sh` |
| PowerShell `Start-Process` | `nohup ... &` |
| `Invoke-RestMethod` | `curl` + `python -c json` |
| `Get-NetTCPConnection` | `ss -tlnp` |
| `$env:VAR = "value"` | `export VAR="value"` (process-scoped) |

Windows scripts in `scripts/dev/` are preserved as legacy reference.

## Safety Rules

- All services bind `127.0.0.1` only (never `0.0.0.0`)
- No port 3001
- No production/staging operations
- No destructive DB operations (`bootstrap-db.sh` only does `upgrade head`)
- No git push
- No secrets in logs
- `cleanup-runtime.sh` never touches PostgreSQL/Redis containers
- PID validation before kill (checks `/proc/PID/cmdline`)

## Troubleshooting

### Worker won't start

```bash
# Check Redis
docker exec amc-dev-redis redis-cli ping

# Check API
curl http://127.0.0.1:8000/health

# Check worker log
tail -30 logs/dev/worker.log
```

### API won't start

```bash
# Check port in use
ss -tlnp | grep :8000

# Check DB
./scripts/dev-linux/check-db.sh

# Check API log
tail -30 logs/dev/api-stub.log
```

### OpenCode won't start

```bash
# Check port in use
ss -tlnp | grep :4096

# Check opencode CLI
opencode --version

# Check log
tail -30 logs/dev/opencode.log
```

### Cleanup stuck processes

```bash
# Force cleanup
./scripts/dev-linux/cleanup-runtime.sh

# If still stuck, manual cleanup
cat .runtime/*.pid 2>/dev/null
kill $(cat .runtime/api.pid) 2>/dev/null
rm -f .runtime/*.pid
```
