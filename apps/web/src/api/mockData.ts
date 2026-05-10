import type {
  AgentSummary,
  EventItem,
  SystemStatus,
  SystemStatusSummary,
  TaskSummary,
  TelegramTopicRead,
} from '../types';

export const mockAgentSummaries: AgentSummary[] = [
  {
    id: 'backend-architect',
    slug: 'backend-architect',
    name: 'Backend Architect',
    role: 'FastAPI / DB / Services',
    status: 'active',
    lastActivity: '2m ago',
  },
  {
    id: 'frontend-developer',
    slug: 'frontend-developer',
    name: 'Frontend Developer',
    role: 'React Dashboard',
    status: 'active',
    lastActivity: '5m ago',
  },
  {
    id: 'devops-automator',
    slug: 'devops-automator',
    name: 'DevOps Automator',
    role: 'Docker / Deploy / Logs',
    status: 'idle',
    lastActivity: '21m ago',
  },
];

export const mockActivity: EventItem[] = [
  { id: 'a1', task_id: 't1', event_type: 'task_completed', actor_type: 'system', actor_id: null, payload: { detail: 'DEV-08B closed' }, created_at: '09:41' },
  { id: 'a2', task_id: 't2', event_type: 'approval_requested', actor_type: 'agent', actor_id: 'backend', payload: { detail: 'Prod deploy gate' }, created_at: '09:36' },
  { id: 'a3', task_id: 't3', event_type: 'memory_retrieved', actor_type: 'system', actor_id: null, payload: { detail: '7 files updated' }, created_at: '09:31' },
];

export const mockTaskSummaries: TaskSummary[] = [
  { id: 'DEV-08C', external_id: 'task-0008', title: 'Frontend foundation', status: 'running', risk_level: 'medium', created_at: '2026-05-10T09:00:00Z' },
  { id: 'SEC-03A', external_id: 'task-0009', title: 'Audit log review', status: 'created', risk_level: 'low', created_at: '2026-05-10T08:30:00Z' },
  { id: 'DEP-02F', external_id: 'task-0010', title: 'Staging smoke', status: 'waiting_approval', risk_level: 'medium', created_at: '2026-05-10T08:00:00Z' },
];

export const mockSystemStatus: SystemStatus = {
  status: 'ok',
  service: 'agent-mission-control-api',
  version: '0.1.0',
  timestamp: new Date().toISOString(),
  checks: {
    api: 'ok',
    database: 'ok',
    redis: 'ok',
  },
};

export const mockSystemStatusSummary: SystemStatusSummary = {
  healthy: true,
  database: 'ok',
  redis: 'ok',
  version: '0.1.0',
};

export const mockTopics: TelegramTopicRead[] = [
  {
    id: 'topic-001',
    chat_id: -1001234567890,
    message_thread_id: 1,
    title: 'General',
    kind: 'general',
    agent_id: null,
    project_id: null,
    is_active: true,
    created_at: '2026-05-09T10:00:00Z',
    updated_at: '2026-05-09T10:00:00Z',
  },
  {
    id: 'topic-002',
    chat_id: -1001234567890,
    message_thread_id: 17,
    title: 'Agent: Backend',
    kind: 'agent',
    agent_id: 'backend-architect',
    project_id: null,
    is_active: true,
    created_at: '2026-05-09T10:01:00Z',
    updated_at: '2026-05-09T10:01:00Z',
  },
  {
    id: 'topic-003',
    chat_id: -1001234567890,
    message_thread_id: 23,
    title: 'Approvals',
    kind: 'approvals',
    agent_id: null,
    project_id: null,
    is_active: true,
    created_at: '2026-05-09T10:02:00Z',
    updated_at: '2026-05-09T10:02:00Z',
  },
];
