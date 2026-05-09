# VPS-02: Base Server Setup for Agent Mission Control

**Date:** 2026-05-09
**Agent:** studio-orchestrator
**Status:** ✅ COMPLETED
**Risk level:** medium (server modifications, no app deploy)

---

## Objective

Prepare VPS 45.130.213.12 for future production deploy of Agent Mission Control. Install packages, Docker, create user, directories, firewall — but NOT deploy the application.

## Server

- **IP:** 45.130.213.12
- **SSH:** root, key-based auth
- **OS:** Ubuntu 24.04.4 LTS (Noble Numbat)
- **Kernel:** 6.8.0-106-generic x86_64
- **systemd:** v255

## What was done

### Step 1: SSH connectivity
- `ssh -o BatchMode=yes root@45.130.213.12 "echo SSH_OK"` → SSH_OK ✅

### Step 2: OS check
- Ubuntu 24.04.4 LTS, x86_64, systemd PID 1 ✅

### Step 3: Resource check
- CPU: 2 vCPU ✅
- RAM: 3.8 GiB total, 3.4 GiB available ✅
- Disk: 40 GB vda, 36 GB free ✅
- Swap: 0 B ⚠️ (deferred to VPS-03)

### Step 4: Package index update
- `apt-get update` ✅

### Step 5: Base packages installed
- ca-certificates, curl, gnupg, git, jq, ufw, htop, unzip, lsb-release — all already present ✅

### Step 6: Docker Engine installed
- Docker GPG key added to `/etc/apt/keyrings/docker.gpg`
- Docker apt repo: `deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu noble stable`
- Installed: docker-ce 29.4.3, docker-ce-cli, containerd.io 2.2.3, docker-buildx-plugin 0.33.0, docker-compose-plugin 5.1.3

### Step 7: Docker enabled
- `systemctl enable --now docker` ✅
- Docker active, version 29.4.3, Compose v5.1.3 ✅

### Step 8: App user created
- `useradd --system --create-home --home-dir /home/agentmc --shell /bin/bash agentmc`
- Added to `docker` group
- UID=999, groups=agentmc(987),docker(988)

### Step 9: Directory structure created
- `/opt/agent-control` — agentmc:agentmc, mode 750
- `/var/log/agentrouter` — agentmc:agentmc, mode 750
- `/var/lib/agentrouter` — agentmc:agentmc, mode 750

### Step 10: Firewall configured
- UFW enabled with `--force`
- OpenSSH (22/tcp) ALLOW IN
- Default: deny incoming, allow outgoing
- HTTP (80) / HTTPS (443) NOT opened (no domain/Caddy yet)

### Step 11: Tool verification
- git ✅, docker ✅, jq ✅, curl ✅, ufw ✅
- Docker 29.4.3 active ✅, Compose v5.1.3 ✅

### Step 12: Deploy verification (negative checks)
- `/opt/agent-control/agentrouter` → REPO_NOT_CLONED ✅
- `.env` → ENV_NOT_CREATED ✅
- Docker containers → 0 ✅

## What was NOT done

- ❌ Repo NOT cloned
- ❌ .env NOT created
- ❌ No secrets entered
- ❌ Application NOT deployed
- ❌ Migrations NOT run
- ❌ Telegram bot NOT started
- ❌ OpenCode NOT started
- ❌ Deploy scripts NOT executed
- ❌ GitHub repo NOT modified
- ❌ No git push
- ❌ No swap configured (deferred)
- ❌ SSH hardening NOT done (deferred)
- ❌ Caddy NOT installed (deferred)
- ❌ Ports 80/443 NOT opened (deferred)

## Known warnings / deferred items

| Item | Severity | Deferred to |
|------|----------|-------------|
| No swap configured | ⚠️ Low | VPS-03 |
| PermitRootLogin yes | ⚠️ Medium | VPS-03 |
| Password auth ambiguous (conflicting sshd configs) | ⚠️ Medium | VPS-03 |
| No domain configured | — | VPS-03 |
| Caddy not installed | — | VPS-03 |
| Ports 80/443 closed | ✅ Intentional | VPS-03 (after domain + Caddy) |

## Server state after VPS-02

| Component | Status |
|-----------|--------|
| Docker Engine | 29.4.3 active |
| Docker Compose | v5.1.3 |
| User agentmc | UID 999, docker group |
| /opt/agent-control | agentmc:agentmc 750 |
| /var/log/agentrouter | agentmc:agentmc 750 |
| /var/lib/agentrouter | agentmc:agentmc 750 |
| UFW | active, SSH only |
| Open ports | 22/tcp (SSH) + 53 (DNS localhost) |
| App containers | 0 |
| Production deploy | NOT executed |

## Recommended VPS-03 next steps

| Phase | Action | Risk |
|-------|--------|------|
| A | Add 2GB swap file | Low |
| B | Harden SSH: disable root login, password auth, add agentmc key | Medium |
| C | Clone repo to /opt/agent-control/agentrouter | Low |
| D | Create .env from .env.example with real secrets | **High** |
| E | Start PostgreSQL + Redis via docker-compose.prod.yml | Medium |
| F | Run Alembic migrations | **High** |
| G | Start API + Worker + Bot via systemd | Medium |
| H | Install Caddy, configure reverse proxy | Medium |
| I | Configure DNS | Medium |
| J | Open ports 80/443 in UFW | Low |
| K | Run preflight + smoke validation | Low |
| L | Production deploy approval gate | **Critical** |

## Production deploy claim

**Production deploy has NOT been executed.** Server is prepared but no application code is running.

## Memory checkpoint

- **Memory updated:** yes
- **Files updated:** PROJECT_MEMORY.md, .ai_memory/current_state.md, .ai_memory/_INDEX.md
- **Commit:** pending (commit message: `docs(vps): record base server setup`)
- **Skipped reason:** n/a
