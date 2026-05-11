# DEV-12B — Local Runner Skeleton CLI

## Summary

Implemented local-only `apps/runner` skeleton CLI with strict boundary checks and explicitly disabled execution capabilities.

## Scope

- Added `agentrouter_runner` package (stdlib-only)
- Added commands: `status`, `doctor`, `check-path --path`
- Added strict root/path utilities and sensitive path classifier
- Added focused pytest suite under `apps/runner/tests`
- Updated docs (`README.md`, `docs/local-runner-roadmap.md`, `apps/runner/README.md`)

## Safety

- No deploy/SSH/migrations/.env updates
- No cloud/API/Telegram/OpenCode integration
- No command execution implementation
- No user project file-content reads
- Tests use temp dirs only

## Validation

- `python -m pytest apps/runner/tests -q` → PASS
- CLI smoke via temp dir script → PASS
- git + diff safety checks run

## Files

- `apps/runner/**` (new skeleton package + tests)
- `README.md`
- `docs/local-runner-roadmap.md`
- `PROJECT_MEMORY.md`
- `.ai_memory/current_state.md`
- `.ai_memory/_INDEX.md`

## Next recommended step

- DEV-12C Runner Pairing/Heartbeat Design, or
- DEV-12C Read-only Project Discovery
