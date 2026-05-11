# apps/web — Telegram Mini App

Vite + React + TypeScript frontend for Agent Mission Control.

## Local Development

```bash
npm install
npm run dev        # http://localhost:5173
```

The app works in browser preview mode without a backend — all API calls fall back to mock data.

## Production Build

```bash
npm ci
npm run build:prod
```

Output: `dist/` with `/app/` base path for deployment under `https://domain/app/`.

Build script: `../../scripts/build-miniapp.sh`

**Do NOT commit `dist/` to git.**

## Scripts

| Script | Purpose |
|--------|---------|
| `npm run dev` | Local dev server (port 5173) |
| `npm run build` | Build with default base `/` |
| `npm run build:prod` | Build with `VITE_BASE_PATH=/app/` |
| `npm run preview` | Preview production build locally |

## Environment Variables (build time)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_BASE_PATH` | `/` | Base path for assets. Set `/app/` for production. |
| `VITE_API_BASE_URL` | `/api` | Backend API base URL. Default works when served from same origin. |

No secrets required at build time.

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | HomePage | Dashboard with status cards, summaries, mode indicator |
| `/workspaces` | WorkspacesPage | Workspace source foundation (Local Runner / Cloud / GitHub) |
| `/agents` | AgentsPage | All registered agents |
| `/agents/new` | CreateAgentPage | Register new agent form (warns about real record creation) |
| `/agents/:id` | AgentDetailPage | Agent details |
| `/tasks` | TasksPage | Task queue with status/risk badges |
| `/tasks/new` | CreateTaskPage | Create task form (warns about real record creation) |
| `/topics` | TopicsPage | Telegram topic bindings with role explanations |
| `/more` | MorePage (Settings) | Safe auth/session info, API mode, guarded-mode explanation |

## Liquid Glass Design System

The UI now uses a token-based **Liquid Glass** foundation in `src/styles.css`:

- CSS custom properties for colors, glass surfaces, spacing, radius, typography, safe-area
- glass primitives: `.glass-card`, `.glass-card--clickable`
- button system: `.liquid-button` with `primary`, `secondary`, `ghost` variants
- section and metric primitives: `.section-header`, `.metric-card`
- refreshed form controls and state components using design tokens

No Tailwind and no new UI library dependencies were introduced.

## Navigation Structure

Bottom navigation now has 5 tabs:

1. Home (`/`)
2. Spaces (`/workspaces`)
3. Agents (`/agents`)
4. Tasks (`/tasks`)
5. More (`/more`)

## Create Flow Safety

- **Confirmation required** before creating agents, tasks, or topic bindings
- Explicit warnings when connected to production API (real record will be created)
- Task/agent creation does **not** start OpenCode or execute commands
- Topic binding registers a mapping only — does **not** create Telegram topics
- Approvals overview on Home dashboard (pending approvals count)

## Security

- Raw `session_token` is **never displayed** in the UI.
- Raw `initData` is **never displayed** in the UI.
- `initDataUnsafe` keys are **not leaked**.
- Auth/session cards show only safe status indicators (verified/preview/failed).
- Session token is stored in-memory only (not persisted to localStorage).
- No secrets are included at build time.

## Features

- Mobile-first iOS-like UI (rounded cards, bottom nav)
- Real backend API integration with mock fallback
- Telegram WebApp SDK integration (initData auth, ready/expand)
- Loading/error/empty/success states on all pages
- Create agent, create task, topic binding forms (with production safety warnings)
- API mode indicator (Live / Preview)
- Safe auth diagnostics (no raw token leakage)

## UI Mode Indicators

| Mode | Description |
|------|-------------|
| Live API (green) | Connected to production API, session active |
| Preview data (gray) | API connected but no active session |
| Preview mode (gray) | Opened outside Telegram, using mock data |
| API unavailable (red) | API health check failed |

## Deployment

See [docs/miniapp-deploy.md](../../docs/miniapp-deploy.md) for full deployment guide.

## Local Runner (design status)

Local Runner is currently **design/contracts only** (DEV-12A):

- Product model: [docs/local-runner-product-model.md](../../docs/local-runner-product-model.md)
- Protocol draft: [docs/local-runner-protocol.md](../../docs/local-runner-protocol.md)
- Security model: [docs/local-runner-security-model.md](../../docs/local-runner-security-model.md)
- API contract draft: [docs/local-runner-api-contract.md](../../docs/local-runner-api-contract.md)
- Roadmap/phases: [docs/local-runner-roadmap.md](../../docs/local-runner-roadmap.md)

Important:
- No real local file access implemented yet
- No File System Access API implementation in Mini App
- No command execution implemented yet
