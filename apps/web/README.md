# apps/web — DEV-08C Frontend Foundation

This folder now contains a real **Vite + React + TypeScript** frontend foundation for Agent Mission Control.

## Implemented

- Vite app scaffold (`index.html`, `vite.config.ts`, `tsconfig*`, `src/*`)
- Mobile-first, iOS-like light UI baseline (rounded cards, soft shadows, sticky bottom nav)
- App routes:
  - `/`
  - `/agents`
  - `/agents/:id`
  - `/tasks`
  - `/more`
- Required UI components:
  - `AppShell`, `BottomNav`, `Header`, `StatusCard`, `AgentCard`, `QuickActionCard`
  - `ActivityItem`, `AgentListItem`, `AgentDetailCard`, `StatusPill`, `PageContainer`
- Telegram WebApp utility with safe browser fallback:
  - Detects `window.Telegram?.WebApp`
  - Calls `ready()` and `expand()` when available
  - Reads `initData` and `initDataUnsafe` safely
- API client layer with local mock fallback for preview/dev

## Scripts

```bash
npm install
npm run dev
npm run build
npm run preview
```

## Notes

- No secrets are used or required for the local UI foundation.
- API methods fall back to mock data when backend endpoints are unavailable.
