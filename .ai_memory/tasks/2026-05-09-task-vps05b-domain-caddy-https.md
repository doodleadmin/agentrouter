# VPS-05B: Domain + Caddy + HTTPS Verification

**Date:** 2026-05-09
**Agent:** studio-orchestrator
**Status:** ✅ COMPLETED
**Risk level:** medium (Caddy install, firewall changes, public HTTPS exposure)

---

## Objective

Verify DNS `polyrouter.ru → 45.130.213.12`, install Caddy, configure reverse proxy `https://polyrouter.ru → http://127.0.0.1:8000`, open 80/443, and verify HTTPS health endpoint — without running migrations or starting OpenCode tasks.

## Server

- **IP:** 45.130.213.12
- **Domain:** polyrouter.ru
- **SSH:** agentmc (app operations), root (system operations)
- **OS:** Ubuntu 24.04.4 LTS

## What was done

### STEP 0: Local safety check
- Local repo: `main` branch, HEAD `a6be871`, synced with `origin/main`, clean tree ✅

### STEP 1: Confirmation gate
- Gate `CONFIRM_VPS05B_HTTPS=yes` confirmed ✅

### STEP 2: DNS verification
- `nslookup polyrouter.ru` → `45.130.213.12` ✅
- `nslookup polyrouter.ru 8.8.8.8` → `45.130.213.12` ✅
- VPS `getent ahosts polyrouter.ru` → `45.130.213.12` STREAM/DGRAM/RAW ✅

### STEP 3: Server baseline
- SSH: agentmc `AGENTMC_SSH_OK`, root `ROOT_FALLBACK_OK` ✅
- Server repo: `main`, HEAD `f456c2a`, clean ✅
- 5 containers: api (healthy), postgres (healthy), redis (healthy), worker (healthy), telegram-bot (healthy) ✅
- UFW: active, 22/tcp only ✅
- Caddy: NOT installed ✅

### STEP 4: API local health before Caddy
- `curl http://127.0.0.1:8000/health` → `{"status":"ok","checks":{"api":"ok","database":"ok","redis":"ok"}}` ✅

### STEP 5: Install Caddy
- `apt-get install -y caddy` → Caddy 2.6.2 ✅
- `systemctl is-enabled caddy` → enabled ✅
- `systemctl is-active caddy` → active ✅

### STEP 6: Configure Caddy
- Caddyfile written to `/etc/caddy/Caddyfile`:
  ```
  polyrouter.ru {
      encode gzip zstd
      reverse_proxy 127.0.0.1:8000
      header {
          X-Content-Type-Options nosniff
          X-Frame-Options DENY
          Referrer-Policy no-referrer
      }
  }
  ```
- `caddy validate` → `Valid configuration` ✅
- `systemctl reload caddy` → active ✅

### STEP 7: Open UFW 80/443
- UFW rules added: 80/tcp ALLOW, 443/tcp ALLOW ✅
- Final UFW: 22/tcp, 80/tcp, 443/tcp allowed (default deny incoming) ✅

### STEP 8: HTTPS verification
- VPS HTTPS: `curl https://polyrouter.ru/health` → `{"status":"ok","checks":{"api":"ok","database":"ok","redis":"ok"}}` ✅
- Local HTTPS: `curl -fsSk https://polyrouter.ru/health` → ok ✅
- Let's Encrypt certificate: obtained successfully (http-01 challenge) ✅
- Local Windows schannel `-fsS` fails with `CRYPT_E_REVOCATION_OFFLINE` — client-side schannel CRL issue, not server issue ✅

### STEP 9: Final runtime check
- All 5 containers: healthy ✅
- Caddy: active ✅
- Listening ports: 22 (ssh), 80 (caddy), 443 (caddy), 8000 (docker-api, 127.0.0.1 only) ✅
- API: accessible via `https://polyrouter.ru/health` ✅

### STEP 10: Telegram smoke status
- Telegram manual smoke: **PASS** (user confirmed @agentrouters_bot responds, from VPS-05A)

## What was NOT done

- ❌ Migrations NOT run (already applied in VPS-04)
- ❌ OpenCode NOT started
- ❌ No real agent executions
- ❌ No deploy scripts executed
- ❌ No git push
- ❌ Secrets NOT printed

## Risks / Warnings

| Item | Severity | Detail |
|------|----------|--------|
| Caddy 2.6.2 (Ubuntu apt) | ⚠️ Low | Slightly older than Caddy 2.7+ with improved TLS. Acceptable; upgrade path available. |
| Windows schannel CRL offline | ⚠️ Info | Local Windows curl `-fsS` fails due to schannel revocation check. Server cert valid, `-k` works. |
| No OCSP stapling | ⚠️ Low | Caddy log warning: "no OCSP server specified in certificate". Let's Encrypt certs may not support OCSP. |

## Production exposure status

| Component | Status |
|-----------|--------|
| HTTPS health endpoint | `https://polyrouter.ru/health` — public ✅ |
| API | `127.0.0.1:8000` — internal only ✅ |
| Telegram bot | @agentrouters_bot — polling ✅ |
| OpenCode runtime | NOT started ✅ |
| Firewall | 22/tcp, 80/tcp, 443/tcp allowed ✅ |

## Recommended next step

**VPS-06: Monitoring, backups, and runtime operations**
- Configure log rotation for Caddy + app logs
- Set up automated DB backups (cron)
- Configure health monitoring (uptime or similar)
- Document current operational procedures

## Memory checkpoint

- **Memory updated:** yes
- **Files updated:** PROJECT_MEMORY.md, .ai_memory/current_state.md, .ai_memory/_INDEX.md
- **Commit:** pending
- **Skipped reason:** n/a
