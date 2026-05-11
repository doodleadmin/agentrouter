# Local Runner Security Model (DEV-12A)

## Security boundary

User selects exactly one allowed root (example: `F:\dev`).

All runner operations must:
1. Normalize path
2. Resolve real path
3. Verify resolved path remains inside allowed root

## Boundary enforcement

Block all path escape techniques:

- `../` traversal
- symlink escape outside root
- junction escape outside root (Windows)
- absolute path outside root

## Default deny paths (unless explicit elevated approval)

- `.env`
- `.env.*`
- `secrets.*`
- `id_rsa`, private keys
- `.ssh/**`
- credential stores
- `.git/config` (unless explicitly approved)
- `node_modules/**` (default deny for heavy trees)
- build artifacts (`dist`, `.next`, etc.) by default

## Secret handling

Runner and cloud logs must store redacted output only.

Redaction classes include:
- Telegram tokens
- API keys
- DB URLs
- Redis URLs
- S3 keys
- private keys
- JWT/session tokens
- Telegram `initData` / `session_token`

Never return full secret values in UI/logs/Telegram outputs.

## Approval classes

- `read_safe`
- `read_sensitive`
- `write_file`
- `delete_file`
- `run_command`
- `network_access`
- `git_commit`
- `git_push`
- `dependency_install`
- `env_access`
- `destructive_action`

## Command safety policy

- Default: command execution disabled
- Enable only via allowlist + approval
- Risk-scoring required

Block or require highest-risk approval for commands like:
- `rm -rf`, `del /s`, format/wipe
- curl/wget pipe-to-shell patterns
- broad chmod/chown
- privileged/sudo-like operations
- registry/system-level destructive changes

Require approval for:
- `npm install`, `pip install`
- `git push`
- production deploy commands

## Audit model

Every runner operation must emit audit event with:
- requester identity
- agent identity
- workspace/runner id
- requested path(s)
- operation type
- approval status
- result status
- redacted logs
- timestamp

## DEV-12A scope boundary

This document defines model only.
No real runner executable, no real local file access, no command execution implemented.
