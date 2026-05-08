# Production Deployment Guide — Agent Mission Control

Version: 1.0
Audience: DevOps / Server Administrator

## Architecture

```
                    Internet
                       |
                  Caddy (443/80)
                  auto-HTTPS + reverse proxy
                       |
              127.0.0.1:8000 (API only)
                       |
         +-------------+-------------+
         |             |             |
    API (FastAPI)  Worker        Telegram Bot
    :8000          (Celery)      (polling)
         |             |
    PostgreSQL     Redis
    (pg16+pgvector) (7-alpine)
```

All services bind to `127.0.0.1` or internal Docker network. Only Caddy exposes ports 80/443 to the internet.

## Required Software

| Package       | Version     | Purpose                          |
|---------------|-------------|----------------------------------|
| Python        | 3.12+       | API, Worker, Bot                 |
| PostgreSQL    | 16 + pgvector | State, task queue results      |
| Redis         | 7+          | Celery broker, caching           |
| Caddy         | 2.x         | Reverse proxy, auto-TLS          |
| Docker        | 24+         | Alternative: containerized deploy |
| Docker Compose| v2          | Multi-container orchestration    |

## Two Deployment Modes

### Mode A: systemd (bare-metal / VM)

Each app runs as a systemd service under a dedicated `agentmc` user.

Files:
- `infra/deploy/agentrouter-api.service`
- `infra/deploy/agentrouter-worker.service`
- `infra/deploy/agentrouter-telegram-bot.service`
- `infra/deploy/Caddyfile`

### Mode B: Docker Compose (containerized)

All services run in containers with an internal network.

File:
- `infra/docker/docker-compose.prod.yml`

## Environment Setup

```bash
# 1. Clone the repo
git clone <repo-url> /opt/agent-control/agentrouter
cd /opt/agent-control/agentrouter

# 2. Create .env from template
cp .env.example .env
chmod 600 .env

# 3. Fill in real values (NEVER commit .env)
#    Required: POSTGRES_PASSWORD, TELEGRAM_BOT_TOKEN,
#              TELEGRAM_ADMIN_USER_IDS, CALLBACK_SECRET
nano .env
```

## File Permissions (Mode A: systemd)

```bash
# Create dedicated user
sudo useradd --system --home /opt/agent-control/agentrouter --shell /bin/false agentmc

# Set ownership
sudo chown -R agentmc:agentmc /opt/agent-control/agentrouter

# Create log directory
sudo mkdir -p /opt/agent-control/agentrouter/logs
sudo chown agentmc:agentmc /opt/agent-control/agentrouter/logs

# Protect .env
sudo chmod 600 /opt/agent-control/agentrouter/.env
sudo chown agentmc:agentmc /opt/agent-control/agentrouter/.env
```

## systemd Install Steps (MANUAL — requires approval)

> **These steps must be run by an administrator on the target server.**
> They are NOT automated by any agent.

```bash
# 1. Copy unit files
sudo cp infra/deploy/agentrouter-api.service     /etc/systemd/system/
sudo cp infra/deploy/agentrouter-worker.service   /etc/systemd/system/
sudo cp infra/deploy/agentrouter-telegram-bot.service /etc/systemd/system/

# 2. Reload systemd
sudo systemctl daemon-reload

# 3. Enable on boot
sudo systemctl enable agentrouter-api agentrouter-worker agentrouter-telegram-bot

# 4. Start in order
sudo systemctl start agentrouter-api
sudo systemctl start agentrouter-worker
sudo systemctl start agentrouter-telegram-bot

# 5. Verify
sudo systemctl status agentrouter-api
sudo systemctl status agentrouter-worker
sudo systemctl status agentrouter-telegram-bot
```

## Caddy Install Steps (MANUAL — requires approval)

```bash
# 1. Install Caddy (Debian/Ubuntu)
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy

# 2. Copy Caddyfile
sudo cp infra/deploy/Caddyfile /etc/caddy/Caddyfile

# 3. Edit domain and email placeholders
sudo nano /etc/caddy/Caddyfile
# Replace {$AGENTROUTER_DOMAIN} with your real domain
# Replace {$AGENTROUTER_TLS_EMAIL} with your email

# 4. Create log directory
sudo mkdir -p /var/log/caddy
sudo chown caddy:caddy /var/log/caddy

# 5. Validate and reload
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

## Docker Compose Deploy (Mode B)

```bash
# 1. Ensure .env is filled
cp .env.example .env && chmod 600 .env

# 2. Build and start
docker compose -f infra/docker/docker-compose.prod.yml up -d --build

# 3. Check status
docker compose -f infra/docker/docker-compose.prod.yml ps

# 4. View logs
docker compose -f infra/docker/docker-compose.prod.yml logs -f api
```

## Startup Order

Services must start in this order due to dependencies:

```
1. PostgreSQL  (or docker compose postgres service)
2. Redis       (or docker compose redis service)
3. API         (depends on PostgreSQL + Redis)
4. Worker      (depends on Redis + API healthy)
5. Telegram Bot(depends on API healthy)
```

## Health Checks

```bash
# API health
curl -s http://127.0.0.1:8000/health | python -m json.tool

# API version
curl -s http://127.0.0.1:8000/version | python -m json.tool

# PostgreSQL
pg_isready -U agentmc -d agentrouter

# Redis
redis-cli ping
```

Expected API health response:
```json
{
  "status": "ok",
  "service": "agent-mission-control-api",
  "version": "0.1.0",
  "timestamp": "2026-05-08T12:00:00+00:00",
  "checks": {
    "api": "ok",
    "database": "ok",
    "redis": "ok"
  }
}
```

When a dependency is unreachable, `"status"` becomes `"degraded"` and the corresponding check shows `"error"`.

## Validation

Before deploying, run the template validation script:

```bash
bash scripts/deploy/validate-production-templates.sh
```

This checks:
- All required files exist
- No real secrets in templates
- No `SQL_ECHO=true` defaults
- No `DEBUG=true` in production configs
- API binds `127.0.0.1` only
- No inline secrets in systemd units
- Script syntax validity

## Rollback Procedure

### systemd rollback

```bash
# 1. Stop services
sudo systemctl stop agentrouter-telegram-bot agentrouter-worker agentrouter-api

# 2. Checkout previous known-good commit
cd /opt/agent-control/agentrouter
git log --oneline -10  # identify rollback target
git checkout <previous-commit>

# 3. Reinstall dependencies (if needed)
cd apps/api && sudo -u agentmc .venv/bin/pip install -e .
cd ../worker && sudo -u agentmc .venv/bin/pip install -e .
cd ../telegram-bot && sudo -u agentmc .venv/bin/pip install -e .

# 4. Run any pending downgrades (if migrations were involved)
cd apps/api
sudo -u agentmc .venv/bin/alembic downgrade -1

# 5. Restart services
sudo systemctl start agentrouter-api
sudo systemctl start agentrouter-worker
sudo systemctl start agentrouter-telegram-bot

# 6. Verify
curl http://127.0.0.1:8000/health
```

### Docker Compose rollback

```bash
# 1. Checkout previous commit
git checkout <previous-commit>

# 2. Rebuild and restart
docker compose -f infra/docker/docker-compose.prod.yml up -d --build

# 3. Verify
curl http://127.0.0.1:8000/health
```
