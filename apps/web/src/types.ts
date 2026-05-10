export type AgentStatus = 'active' | 'idle' | 'offline';

export interface Agent {
  id: string;
  name: string;
  role: string;
  status: AgentStatus;
  projectCount: number;
  lastActivity: string;
}

export interface Activity {
  id: string;
  title: string;
  detail: string;
  time: string;
}

export interface TaskItem {
  id: string;
  title: string;
  risk: 'low' | 'medium' | 'high';
  status: 'queued' | 'running' | 'waiting_approval';
}

export interface SystemStatus {
  onlineAgents: number;
  queuedTasks: number;
  approvalsPending: number;
}
