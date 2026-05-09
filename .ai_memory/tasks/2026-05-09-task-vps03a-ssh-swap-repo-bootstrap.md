# 2026-05-09 — VPS-03A: SSH hardening + swap + repo bootstrap (VPS 45.130.213.12)

- **Agent:** devops-automator
- **Scope:** Real VPS changes (approved gate CONFIRM_VPS03A=yes)
- **Host:** `45.130.213.12` (`eddmiqmrwe`)
- **Safety constraints honored:** no `.env` creation, no deploy, no migrations, no bot/opencode/app run, no 80/443 open, no Caddy install.

## Actions executed

1. Verified root SSH connectivity.
2. Added 2G swap (`/swapfile`) and persisted in `/etc/fstab`.
3. Prepared `agentmc` SSH access by copying root authorized keys and fixing permissions.
4. Verified `agentmc` key login and Docker access before hardening.
5. Applied SSH hardening drop-in:
   - `PasswordAuthentication no`
   - `KbdInteractiveAuthentication no`
   - `PermitRootLogin prohibit-password`
   - `PubkeyAuthentication yes`
6. Validated SSH config (`sshd -t`), reloaded service, and re-verified both `agentmc` and root key login.
7. Cloned repository to `/opt/agent-control/agentrouter` as `agentmc` and fixed ownership.
8. Verified repo state and commit history.
9. Verified no `.env`, no app containers, and no `agentrouter` services.
10. Checked firewall and listening ports (read-only).

## Key evidence

- Root SSH: `ROOT_SSH_OK`, `root`, `eddmiqmrwe`
- Swap active: `/swapfile file 2G`
- Agent user SSH: `AGENTMC_SSH_OK`, `DOCKER_OK`
- After hardening: `AGENTMC_AFTER_HARDENING_OK`, `ROOT_KEY_FALLBACK_OK`
- Repo branch: `main`
- Latest commit: `6530db3` (next `7f51829`)
- `.env` check: `ENV_NOT_CREATED`
- Running containers: none
- Agentrouter systemd services: none
- UFW: active, only `22/tcp` allowed inbound

## Result

VPS-03A completed successfully with required safety constraints preserved.
