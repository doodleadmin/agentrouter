# DEV-12A: Local Runner Protocol Design + Safety Model

**Date:** 2026-05-11
**Agent:** studio-orchestrator
**Contour:** design/contracts only, local docs + frontend non-executing types

## Goal
Design Local Runner architecture for safe local workspace integration (example allowed root: `F:\dev`) without implementing real runner execution.

## Outputs created

- `docs/local-runner-product-model.md`
- `docs/local-runner-protocol.md`
- `docs/local-runner-security-model.md`
- `docs/local-runner-api-contract.md`
- `docs/local-runner-roadmap.md`

## Supporting updates

- `apps/web/src/types.ts` — non-executing runner/protocol type definitions
- `apps/web/src/pages/WorkspacesPage.tsx` — Local Runner safety copy aligned with protocol model
- `apps/web/README.md` and root `README.md` — references to Local Runner docs

## Key decisions

1. **Outbound-only runner connectivity** recommended for MVP (polling or runner-initiated WebSocket).
2. **Allowed-root boundary** is mandatory; all resolved paths must remain inside selected root.
3. **Approval-first model** for sensitive reads, all writes, and future command execution.
4. `apply-patch` and `run-command` are **future** and approval-gated in API contract draft.
5. DEV-12A explicitly excludes real local file access, runner executable implementation, and command execution.

## Validation

- Frontend touched → builds executed:
  - `npm run build` ✅ PASS
  - `npm run build:prod` ✅ PASS

## Safety

- No deploy
- No VPS changes
- No `.env` / Caddy changes
- No service restarts
- No migrations
- No Telegram manual sends
- No topic creation
- No OpenCode
- No real tasks
- No secrets/raw `initData`/`session_token` printed

## Recommended next step

- DEV-12B Runner Skeleton CLI (Phase 1), or
- DEV-12B Telegram Group Connect Flow

## Memory checkpoint

- **Memory updated:** yes
- **Files updated:** PROJECT_MEMORY.md, .ai_memory/current_state.md, .ai_memory/_INDEX.md, this task log
- **Commit hash:** pending (no commit in this run)
