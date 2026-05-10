# DEV-09A: Mini App Production UX Polish + Safe Read-only Dashboards

**Date:** 2026-05-10
**Status:** completed
**Agent:** studio-orchestrator
**Risk:** low (local frontend code only, no deploy, no infrastructure changes)

## Goal
Improve Telegram Mini App production UX after successful VPS-08I smoke — remove sensitive display risks, improve dashboards, add production safety copy.

## Implementation

### 1. Removed raw token/initData display risk (CRITICAL)
- **MorePage.tsx**: Completely redesigned.
  - Removed "Init data" card (was showing raw `initData.slice(0, 60)`).
  - Removed "Unsafe payload keys" card (was showing `initDataUnsafe` keys).
  - Replaced "Auth session" card (was showing raw `session_token.slice(0, 8)`).
  - New safe cards: Telegram WebApp detection, Auth status (verified/preview/failed/unavailable), Session status (active/unavailable).
  - Added System diagnostics: API mode indicator (Live/Preview/Error), system status grid, public URL.
  - Added "Topic Bindings" navigation card.

### 2. Improved Home dashboard
- **HomePage.tsx**: Enhanced with:
  - Green/gray mode indicator pill (Live API / Preview data / Preview mode).
  - Guide grid: agent count + active, task count + pending, events count.
  - Quick action cards show "creates a real record" warning when API is connected.
  - Updated to use LoadingState/EmptyState/ErrorState components consistently.
  - Telegram WebApp detection shown in mode indicator.

### 3. Improved read-only pages
- **AgentsPage.tsx**:
  - Added active agent count in subtitle.
  - Updated to use ErrorState component with retry.
  - Added production safety note when API connected.
- **TasksPage.tsx**:
  - Added task count + pending count in subtitle.
  - Updated to use ErrorState component with retry.
  - Added production safety note when API connected.
- **TopicsPage.tsx**:
  - Added topic role explanation cards (all 5 kinds with descriptions).
  - Updated to use LoadingState/EmptyState/ErrorState.
  - Added production safety note when API connected.
- **AgentDetailPage.tsx**: Unchanged (already had reasonable states).

### 4. Create flow safety copy
- **AgentForm.tsx**: Added production warning banner when API connected.
- **TaskForm.tsx**: Added production warning banner when API connected + preview mode banner when not connected.
- **TopicBindingForm.tsx**: Already had disclaimer; added production warning banner.

### 5. API mode indicator
- API mode determined from token presence + system health status.
- Status bar in HomePage shows live/preview mode.
- MorePage shows detailed API mode with color-coded pills.

### 6. UI polish
- **BottomNav.tsx**: "More" → "Settings" label.
- **StatusCard.tsx**: Normalized heading levels for consistent spacing.
- All read-only pages use consistent LoadingState/EmptyState/ErrorState components.

## Files changed

| File | Change |
|------|--------|
| `apps/web/src/pages/MorePage.tsx` | Complete redesign — removed raw token/initData display, added safe auth/session/system cards |
| `apps/web/src/pages/HomePage.tsx` | Enhanced dashboard — mode indicator, summary grids, safety copy, improved states |
| `apps/web/src/pages/AgentsPage.tsx` | Improved states, active count, production safety note |
| `apps/web/src/pages/TasksPage.tsx` | Improved states, task counts, production safety note |
| `apps/web/src/pages/TopicsPage.tsx` | Added role explanation cards, improved states, production safety note |
| `apps/web/src/components/forms/AgentForm.tsx` | Added production safety warning |
| `apps/web/src/components/forms/TaskForm.tsx` | Added production + preview mode safety warnings |
| `apps/web/src/components/forms/TopicBindingForm.tsx` | Added production safety warning |
| `apps/web/src/components/BottomNav.tsx` | More → Settings label |
| `apps/web/src/components/StatusCard.tsx` | Normalized headings |
| `apps/web/README.md` | Updated with security section, mode indicators, page descriptions |

**Total:** 11 files, +429 lines, -88 lines

## Tests / Build

| Command | Result |
|---------|--------|
| `npm run build` | ✅ PASS (TypeScript + Vite, 0 errors, 61 modules) |
| `npm run build:prod` | ✅ PASS (TypeScript + Vite, `/app/` base, 0 errors, 61 modules) |

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

- Secret patterns (Telegram token, DB/Redis URLs, Callback Secret, S3 keys, Healthchecks URL): **no matches** in changed files.
- Raw `session_token`/`initData` values: **no matches** in changed files.
- `apps/web/dist` not staged ✅
- `node_modules` not staged ✅

## Recommended next steps

1. Commit DEV-09A changes (`feat(miniapp): production ux polish, remove sensitive display risks`)
2. Push to GitHub
3. Controlled Mini App deploy to production (`/app/`) if approved
4. Retest WebApp auth smoke after deploy
