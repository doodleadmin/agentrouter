# infra/deploy — Production deployment configurations

## Files

| File | Purpose |
|------|---------|
| `Caddyfile` | Caddy reverse proxy template (auto-HTTPS, TLS, API routing) |
| `agentrouter-api.service` | systemd unit for FastAPI API server |
| `agentrouter-worker.service` | systemd unit for Celery worker |
| `agentrouter-telegram-bot.service` | systemd unit for Telegram bot (polling) |

## Usage

All files are **templates** with placeholders. Before deploying:

1. Copy `.env.example` to `.env` and fill in real values
2. Edit `Caddyfile` — replace `{$AGENTROUTER_DOMAIN}` and `{$AGENTROUTER_TLS_EMAIL}`
3. Run validation: `bash scripts/deploy/validate-production-templates.sh`
4. Follow steps in [docs/deployment.md](../../docs/deployment.md)

## See also

- [Deployment guide](../../docs/deployment.md) — full production setup instructions
- [Operations runbook](../../docs/operations-runbook.md) — start/stop/logs/troubleshooting
- [Deployment policy](../../docs/deployment-policy.md) — approval workflow and safety rules
- [Production Docker Compose](../docker/docker-compose.prod.yml) — containerized deploy mode

## Deploy scripts (DOP-04 Phase 2)

Repository-level deploy helper scripts:

- `scripts/deploy/preflight.sh`
- `scripts/deploy/release.sh`
- `scripts/deploy/rollback.sh`
- `scripts/deploy/smoke.sh`

All scripts default to `DRY_RUN=true` and are intended for safe validation-first operations.
