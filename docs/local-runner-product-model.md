# Local Runner Product Model (DEV-12A)

## What is Local Runner

Local Runner is a small user-side app/CLI that runs on the user's computer and safely bridges local filesystem access to Agent Mission Control.

- Example chosen root: `F:\dev`
- Cloud WebUI / Telegram Mini App **cannot** directly access local folders
- Access happens only through Runner protocol operations
- Runner is outbound-only to cloud (no inbound port required)

## Main user flow

1. User opens **Workspaces** in Mini App/WebUI
2. Clicks **Connect Local Runner**
3. Downloads/starts runner app/CLI
4. Runner starts pairing (pairing code or browser pairing link)
5. User selects allowed root (example: `F:\dev`)
6. Runner registers with cloud and appears online
7. User chooses active project folder under root
8. Agents can request safe read/edit operations through approvals

## Workspace source modes

- `local_runner`
- `cloud_workspace`
- `github_repository`

## Relationship with Telegram topics

- **General topic** = orchestrator input
- **One agent = one topic**
- Tasks in agent topics can reference active workspace/project
- Runner operations are reflected in approvals and system logs

## Non-goals for first implementation

- No automatic command execution
- No unrestricted filesystem access
- No reads outside allowed root
- No secret dumping
- No destructive background actions
- No direct browser filesystem access

## UX status in DEV-12A

DEV-12A provides design/contracts only. Real runner connection, file access, patch apply, and command run are future phases.
