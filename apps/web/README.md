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
| `/` | HomePage | Dashboard overview |
| `/agents` | AgentsPage | All registered agents |
| `/agents/new` | CreateAgentPage | Register new agent form |
| `/agents/:id` | AgentDetailPage | Agent details |
| `/tasks` | TasksPage | Task queue and status |
| `/tasks/new` | CreateTaskPage | Create task form |
| `/topics` | TopicsPage | Telegram topic bindings |
| `/more` | MorePage | Environment info |

## Deployment

See [docs/miniapp-deploy.md](../../docs/miniapp-deploy.md) for full deployment guide.

## Features

- Mobile-first iOS-like UI (rounded cards, bottom nav)
- Real backend API integration with mock fallback
- Telegram WebApp SDK integration (initData auth, ready/expand)
- Loading/error/empty/success states on all pages
- Create agent, create task, topic binding forms
