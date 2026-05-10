import type { Activity, Agent, SystemStatus, TaskItem } from '../types';

export const mockAgents: Agent[] = [
  {
    id: 'backend-architect',
    name: 'Backend Architect',
    role: 'FastAPI / DB / Services',
    status: 'active',
    projectCount: 3,
    lastActivity: '2m ago',
  },
  {
    id: 'frontend-developer',
    name: 'Frontend Developer',
    role: 'React Dashboard',
    status: 'active',
    projectCount: 2,
    lastActivity: '5m ago',
  },
  {
    id: 'devops-automator',
    name: 'DevOps Automator',
    role: 'Docker / Deploy / Logs',
    status: 'idle',
    projectCount: 4,
    lastActivity: '21m ago',
  },
];

export const mockActivity: Activity[] = [
  { id: 'a1', title: 'Task completed', detail: 'DEV-08B closed', time: '09:41' },
  { id: 'a2', title: 'Approval requested', detail: 'Prod deploy gate', time: '09:36' },
  { id: 'a3', title: 'Memory indexed', detail: '7 files updated', time: '09:31' },
];

export const mockTasks: TaskItem[] = [
  { id: 'DEV-08C', title: 'Frontend foundation', risk: 'medium', status: 'running' },
  { id: 'SEC-03A', title: 'Audit log review', risk: 'low', status: 'queued' },
  { id: 'DEP-02F', title: 'Staging smoke', risk: 'medium', status: 'waiting_approval' },
];

export const mockSystemStatus: SystemStatus = {
  onlineAgents: 6,
  queuedTasks: 9,
  approvalsPending: 2,
};
