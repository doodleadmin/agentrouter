# DEV-10A: Safe Production Create Flows + Approval UX

**Date:** 2026-05-10
**Status:** completed
**Agent:** studio-orchestrator
**Risk:** low (local frontend only, no deploy, no infrastructure changes)

## Goal
Improve production Mini App create flows with explicit confirmation UX and add read-only approvals visibility.

## Implementation

### 1. Reusable Confirmation Component
- **ConfirmSubmitCard.tsx** (new): Reusable confirmation card with:
  - Title + summary items (label/value pairs)
  - Warning banner (production/record creation)
  - Secondary note (what it doesn't do)
  - Cancel + Confirm buttons with submitting state

### 2. Harden Create Flows with Confirmation
- **CreateAgentPage.tsx**: Two-step flow — form submit shows confirmation card before actual API call.
  - Confirmation shows: name, role, slug, model
  - Warning: "creates a real agent record" (Live API) or "mock record" (Preview)
  - Note: "This will not start OpenCode or execute any commands."
- **CreateTaskPage.tsx**: Two-step flow — form submit shows confirmation card before actual API call.
  - Confirmation shows: title, risk level, assigned agent
  - Warning: "creates a real task record" (Live API) or "mock record" (Preview)
  - Note: "This will not run the task, start OpenCode, or execute any commands."
  - Extra note for medium/high risk: "require approval before execution"
- **TopicsPage.tsx**: Two-step flow — form submit shows confirmation card before actual API call.
  - Confirmation shows: Chat ID, Thread ID, Title, Kind, Agent
  - Warning: "creates a real topic mapping record" or "mock record"
  - Note: "Create the topic manually in Telegram first, then register the mapping here."
  - Improved empty state: setup instructions for manual topic creation

### 3. Approvals UX
- **ApprovalsCard.tsx** (new): Read-only approvals overview card.
  - Shows pending count badge
  - Lists recent approvals with action + status
  - Empty state: explains approval workflow
  - Loading state with spinner
- **HomePage.tsx**: Added approvals section with pending count in overview grid.
  - Summary grid now shows: agents, tasks, pending approvals
  - ApprovalsCard integrated with loading/error/success states
  - Mode indicator updated: "Guarded mode" when token present

### 4. Guarded-mode copy
- **MorePage.tsx**: Added "Production mode" section with "Guarded mode" card.
  - Explains: create records only, dangerous actions require approval
  - Task creation does not trigger OpenCode or command execution
- **HomePage.tsx**: Status bar shows "Guarded mode" when connected

### 5. UI copy improvements
- Empty state for Topics: setup instructions for manual Telegram topic creation
- Approval card empty: "No approval requests yet. Dangerous actions will appear here."
- Create flows: clear "does not execute" messaging on all three forms

## Files changed

| File | Change |
|------|--------|
| `apps/web/src/components/ConfirmSubmitCard.tsx` | NEW — reusable confirmation component |
| `apps/web/src/components/ApprovalsCard.tsx` | NEW — read-only approvals overview card |
| `apps/web/src/pages/CreateAgentPage.tsx` | Rewritten — two-step with confirmation |
| `apps/web/src/pages/CreateTaskPage.tsx` | Rewritten — two-step with confirmation |
| `apps/web/src/pages/TopicsPage.tsx` | Rewritten — two-step with confirmation, improved empty state |
| `apps/web/src/pages/HomePage.tsx` | Added approvals card + guarded-mode indicator |
| `apps/web/src/pages/MorePage.tsx` | Added guarded-mode explanation card |
| `apps/web/README.md` | Added Create Flow Safety section |

**Total:** 8 files (2 new, 6 modified)

## Tests / Build

| Command | Result |
|---------|--------|
| `npm run build` | ✅ PASS (tsc + vite, 0 errors, 63 modules) |
| `npm run build:prod` | ✅ PASS (tsc + vite `--base /app/`, 0 errors) |

No backend code changed — no backend tests required.

## Safety confirmations

- No deploy ✅
- No VPS changes ✅
- No `.env`/`.env.local` changes ✅
- No Caddy changes ✅
- No services restarted ✅
- No migrations ✅
- No Telegram messages sent ✅
- No Telegram topics created ✅
- OpenCode not started ✅
- Real tasks not run ✅
- Secrets not printed ✅
- Raw `initData` not printed ✅
- Raw `session_token` not printed ✅

## Security grep results

- Secret patterns: **no matches** in changed files
- Raw `session_token`/`initData` values: **no matches** in changed files
- `apps/web/dist` not staged ✅
- `node_modules` not staged ✅

## Recommended next steps

1. Commit DEV-10A (`feat(miniapp): add safe confirmation and approvals ux`)
2. Push to GitHub
3. Controlled Mini App deploy to production (`/app/`) if approved
4. Verify confirmation UX and approvals in production smoke
