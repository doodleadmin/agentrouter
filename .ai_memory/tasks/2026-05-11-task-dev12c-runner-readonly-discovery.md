# DEV-12C — Local Runner Read-only Discovery (metadata-only)

Date: 2026-05-11  
Agent: backend-architect  
Status: completed

## Summary

Implemented DEV-12C in `apps/runner` as a local-only, metadata-only discovery extension on top of DEV-12B. Added project listing, project tree metadata, and safe path stat commands while preserving strict allowed-root confinement and disabled execution/content features.

## Changes

- Added `apps/runner/agentrouter_runner/discovery.py`:
  - dataclasses: `ProjectInfo`, `TreeEntry`, `PathStat`
  - functions: `list_projects`, `build_tree`, `stat_path`
  - metadata-only behavior (no file content reads)
  - depth limiting and generated-dir skipping for tree listing
  - root boundary enforcement using existing `paths.py` helpers
- Updated `apps/runner/agentrouter_runner/cli.py`:
  - new commands: `list-projects`, `tree`, `stat`
  - JSON/human output parity with existing style
  - clear error payloads and non-zero exit code (`2`) for boundary/validation errors
- Added tests:
  - `apps/runner/tests/test_discovery.py`
  - extended `apps/runner/tests/test_cli.py` for discovery smoke
- Updated docs:
  - `apps/runner/README.md`
  - `docs/local-runner-roadmap.md`
  - root `README.md`

## Validation

- `python -m pytest apps/runner/tests -q` → `16 passed, 1 skipped`
- temp-dir CLI smoke PASS for:
  - `status`
  - `doctor`
  - `list-projects`
  - `tree --project ... --max-depth ...`
  - `stat --path ...`
- quick safety scan over changed areas: no key-like token signatures found

## Safety/Constraints check

- No file content read/write features for user projects added.
- No command execution feature added.
- No cloud/pairing/heartbeat/OpenCode/Telegram integrations added.
- Root boundary enforcement preserved via existing path helpers.
- Tests/smoke used temporary directories only.
- No commit/push performed.
