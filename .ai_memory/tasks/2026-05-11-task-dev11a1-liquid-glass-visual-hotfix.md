# 2026-05-11 — DEV-11A.1: Liquid Glass visual hotfix after mobile smoke

- **Agent:** frontend-developer
- **Contour:** local frontend/docs/memory only, no backend/API changes, no deploy
- **Trigger:** real iPhone Telegram Mini App smoke after VPS-11A showed low text contrast, muddy/dark glass overlay, and bottom navigation that did not feel persistently floating/fixed.

## Problems found in mobile smoke

- headings and subtitles looked too dim on iPhone
- muted/supporting text lost readability inside light glass cards
- background/overlay wash made the whole interface feel grey and heavy
- bottom navigation needed stronger floating/fixed capsule treatment and safer bottom clearance

## Fixes made

- updated `apps/web/src/styles.css` tokens for stronger readability:
  - darker readable text tokens
  - lighter surfaces and hover states
  - softer, cleaner light background gradient
  - reduced overlay intensity / muddy wash
- reinforced Telegram iOS-like floating tab bar:
  - fixed capsule nav with stronger white translucency
  - safe-area-aware insets and larger content bottom padding
  - clearer active state and higher z-index
- improved page readability on key screens:
  - Home
  - Workspaces
  - Agents
  - shared `States`, `ApprovalsCard`, `StatusCard`

## Validation

- `npm run build` ✅ PASS
- `npm run build:prod` ✅ PASS

## Safety

- no deploy
- no VPS changes
- no `.env` / Caddy changes
- no service restarts
- no migrations
- no Telegram messages
- no Telegram topics created
- no local file access
- no cloud containers
- no GitHub integration
- no OpenCode
- no command execution
- no raw `initData` / `session_token` output

## Recommended next step

- commit/push DEV-11A.1, then do controlled redeploy as VPS-11B visual hotfix
