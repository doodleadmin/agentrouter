# Local Runner Roadmap (DEV-12A)

## Phase 0 — Protocol/design only
- Product model, protocol, security boundary, API contract draft
- No runner executable
- No real file access

## Phase 1 — Runner skeleton ✅ implemented locally (DEV-12B)
- CLI/app starts locally
- Accepts `--root`
- Normalizes and validates root
- Prints safe status only
- No cloud connection yet

## Phase 2 — Pairing + heartbeat
- Runner pairs with cloud
- Runner appears online in WebUI
- Heartbeats + basic status

## Phase 3 — Read-only project discovery
- List project folders under allowed root
- List tree + read non-sensitive files
- No writes

## Phase 4 — Patch proposal
- Agent proposes diff/patch only
- User sees preview and safety flags
- No patch apply yet

## Phase 5 — Approval-gated file edits
- Apply patch only after explicit approval
- Audit events for every write/delete

## Phase 6 — Plan-only command suggestions
- Suggest and explain commands
- No execution

## Phase 7 — Approval-gated command execution
- Allowlist + risk scoring
- Explicit approval required

## Phase 8 — Git workflow integration
- Branch/commit/diff support
- Push only with approval

## Phase 9 — Agent orchestration integration
- General topic intake
- One agent = one topic workflow
- Runner executes only approved operations

## Key principle across all phases

Outbound-only runner connectivity, strict allowed-root boundary, and approval-first execution model.
