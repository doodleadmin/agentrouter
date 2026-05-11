# Local Runner Skeleton CLI (DEV-12B / DEV-12C)

This folder contains a **local-only skeleton** for Local Runner.

## Scope implemented

- argparse CLI commands:
  - `status`
  - `doctor`
  - `check-path --path <requested>`
  - `list-projects`
  - `tree --project <name> [--max-depth N]`
  - `stat --path <requested>`
- strict allowed-root boundary checks
- sensitive path classification helpers
- skeleton status model with disabled capabilities
- metadata-only discovery (no content reads)

## Explicit non-capabilities (by design)

- no cloud connection
- no pairing/heartbeat
- no Telegram/OpenCode integration
- no file content reads
- no file writes
- no command execution
- no deploy/SSH/migrations/env handling

`tree` and `stat` return metadata only (path/type/size/mtime/extension/flags).

## Usage

From repository root:

```bash
python -m agentrouter_runner --root "<allowed-root>" status
python -m agentrouter_runner --root "<allowed-root>" doctor
python -m agentrouter_runner --root "<allowed-root>" check-path --path "apps/api"
python -m agentrouter_runner --json --root "<allowed-root>" check-path --path "../outside"
python -m agentrouter_runner --json --root "<allowed-root>" list-projects
python -m agentrouter_runner --json --root "<allowed-root>" tree --project "apps" --max-depth 2
python -m agentrouter_runner --json --root "<allowed-root>" stat --path "apps/runner/README.md"
```

If module import path is not configured, set:

```bash
set PYTHONPATH=apps/runner
```

## Safety notes

- blocks traversal (`../`)
- blocks absolute paths outside root
- detects symlink/junction escapes where path resolution can detect them
- flags sensitive/default-deny patterns (`.env`, keys, credentials, `.git/config`, generated dirs)

## Future phases

Aligned with `docs/local-runner-roadmap.md`:

- Phase 2: pairing + heartbeat
- Phase 3: read-only discovery ✅ (DEV-12C metadata-only)
- Phase 4+: proposal/apply/approval workflows
