# DEV-08E: Create Agent / Create Task Flows + Topic Binding UX

**Date:** 2026-05-10
**Status:** completed
**Agents:** studio-orchestrator
**Risk:** low (local code only)

## Summary

Added create-agent, create-task, and topic-binding UX flows to the Telegram Mini App frontend. All flows support real backend API with mock fallback, loading/error/success states.

## Changes

### 1. Types (apps/web/src/types.ts)
- Added `TelegramTopicRead`, `TopicKind`, `TOPIC_KINDS`, `TOPIC_KIND_LABELS`, `TOPIC_KIND_DESCRIPTIONS`
- Added `AgentCreatePayload`, `TaskCreatePayload`, `TelegramTopicCreatePayload`
- Added `FormState` type for form submissions

### 2. API Client (apps/web/src/api/client.ts)
- `createAgent(payload)` — POST /agents with mock fallback
- `createTask(payload)` — POST /tasks with mock fallback
- `getTelegramTopics()` — GET /telegram/topics with mock fallback
- `createTelegramTopic(payload)` — POST /telegram/topics with mock fallback

### 3. Mock Data (apps/web/src/api/mockData.ts)
- Added `mockTopics` array (3 items: General, Agent: Backend, Approvals)

### 4. Create Agent Flow
- **AgentForm** (`components/forms/AgentForm.tsx`): form with name, slug, role, system_prompt, model fields
- **CreateAgentPage** (`pages/CreateAgentPage.tsx`): form page with submit → success → navigate to /agents
- Entry points: AgentsPage "+ Register Agent" button, HomePage "Register agent" quick action

### 5. Create Task Flow
- **TaskForm** (`components/forms/TaskForm.tsx`): form with title, description, risk_level select, agent_id select
- **CreateTaskPage** (`pages/CreateTaskPage.tsx`): loads agents, form with submit → success → navigate to /tasks
- Supports `?agent_id=` query param to preselect agent
- Entry points: TasksPage "+ Create Task" button, HomePage "Create task" quick action, AgentDetailPage "Create task for this agent"

### 6. Topic Binding UX
- **TopicMappingCard** (`components/TopicMappingCard.tsx`): displays existing topic mapping with kind badge and details
- **TopicBindingForm** (`components/forms/TopicBindingForm.tsx`): form with chat_id, thread_id, title, kind select, conditional agent_id
- **TopicsPage** (`pages/TopicsPage.tsx`): existing mappings list + registration form toggle
- Clear disclaimer: "This only registers a mapping — it does NOT create a Telegram topic"
- Client-side validation: agent kind requires agent_id, task kind requires project_id
- Entry point: MorePage "Topic Bindings" card

### 7. Navigation Updates
- App.tsx: added routes `/agents/new`, `/tasks/new`, `/topics`
- HomePage: quick actions now navigate to `/tasks/new` and `/agents/new`
- AgentsPage: added "+ Register Agent" button
- TasksPage: added "+ Create Task" button
- AgentDetailPage: added "Create task for this agent" button
- MorePage: added "Topic Bindings" card linking to `/topics`

### 8. Form Styles (apps/web/src/styles.css)
- Added `.form-label`, `.form-input`, `.form-textarea`, `.form-submit`
- Added `.form-error`, `.form-success`, `.form-disclaimer`
- Consistent iOS-like card style with indigo submit buttons

## Test Results

| Suite | Tests | Status |
|-------|-------|--------|
| API — auth/topics/policy | 37 | ✅ PASS |
| Telegram bot | 83 | ✅ PASS |
| Worker | 98 | ✅ PASS |
| Frontend build | — | ✅ PASS |

## Files Changed

**New files (7):**
- `apps/web/src/components/forms/AgentForm.tsx`
- `apps/web/src/components/forms/TaskForm.tsx`
- `apps/web/src/components/forms/TopicBindingForm.tsx`
- `apps/web/src/components/TopicMappingCard.tsx`
- `apps/web/src/pages/CreateAgentPage.tsx`
- `apps/web/src/pages/CreateTaskPage.tsx`
- `apps/web/src/pages/TopicsPage.tsx`

**Modified files (10):**
- `apps/web/src/types.ts`
- `apps/web/src/api/client.ts`
- `apps/web/src/api/mockData.ts`
- `apps/web/src/App.tsx`
- `apps/web/src/styles.css`
- `apps/web/src/pages/HomePage.tsx`
- `apps/web/src/pages/AgentsPage.tsx`
- `apps/web/src/pages/TasksPage.tsx`
- `apps/web/src/pages/AgentDetailPage.tsx`
- `apps/web/src/pages/MorePage.tsx`

## Backend Changes
- None. All changes are frontend-only.

## Risks
- None: local code only, no deploy, no migrations, no secrets

## Contour
- Local code changes only (frontend)
- No backend changes
- No migrations
- No deploy
- No secrets edits
- Production not touched
