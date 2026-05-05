# BE-11: Scripts Final Repair — COMPLETE

**Date:** 2026-05-05
**Agent:** studio-orchestrator
**Risk:** low
**Scope:** local only; scripts only; no deploy/migrations/secrets/OpenCode.

## Summary

BE-11 scripts (`start-opencode.ps1`, `start-api-opencode.ps1`, `smoke-real-opencode-runtime.ps1`, `cleanup-runtime.ps1`) verified and confirmed PSParser + DryRun PASS for all 4 scripts. No code changes needed — existing fixes already applied during BE-11B/C iteration hold.

## Root Cause of Prior Failures

1. **start-opencode.ps1 hang**: `Start-Process -NoNewWindow` with parent pipe inheritance caused script to not exit. Fixed with `cmd /c start "" /min` fully detached strategy.
2. **PSParser vs Runtime mismatch**: Em dash Unicode chars (U+2014, U+2500) passed PSParser tokenizer but failed at runtime. All replaced with ASCII hyphens.
3. **PS 5.1 incompatibility**: `??` null-coalescing operator (PowerShell 7+ only) replaced with `if/else` blocks.
4. **cleanup-runtime.ps1 `elseif`**: Encoding artifact from edit operations caused extra closing braces. Fixed by rewriting `elseif` to nested `if/else`.

## Script Status

| Script | UTF-8 no BOM | PSParser | DryRun | Safety |
|--------|-------------|----------|--------|--------|
| `start-opencode.ps1` | YES | PASS | PASS | 127.0.0.1 only |
| `start-api-opencode.ps1` | YES | PASS | PASS | no .env writes |
| `smoke-real-opencode-runtime.ps1` | YES | PASS | PASS | worker bypass explicit |
| `cleanup-runtime.ps1` | YES | PASS | PASS | no docker compose down -v |

## Safety Verified

- No `0.0.0.0` bind — all listener checks confirm `127.0.0.1` only
- No port `3001` — only 4096 (OpenCode) and 8000 (API)
- No `.env` writes — only comments stating "do NOT edit .env"
- No persistent env writes — process-scoped only
- No `docker compose down -v` — only safe process stop
- DryRun does NOT start processes

## Files Changed
- `scripts/dev/start-opencode.ps1` (rewritten: detach + ALREADY_RUNNING)
- `scripts/dev/start-api-opencode.ps1` (em dash fix, Python config via temp file)
- `scripts/dev/smoke-real-opencode-runtime.ps1` (?? fix, stub fingerprints check)
- `scripts/dev/cleanup-runtime.ps1` (elseif fix, safe stop only)

## Next Steps
- Commit BE-11 scripts as separate commit
- BE-12 already committed (`1dedfe3`)
