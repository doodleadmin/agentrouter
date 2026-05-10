import { mockActivity, mockAgents, mockSystemStatus, mockTasks } from './mockData';
import type { Activity, Agent, SystemStatus, TaskItem } from '../types';

const API_BASE = '/api';

async function safeFetch<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

export const api = {
  getSystemStatus: (): Promise<SystemStatus> => safeFetch('/status', mockSystemStatus),
  getAgents: (): Promise<Agent[]> => safeFetch('/agents', mockAgents),
  getAgentById: async (id: string): Promise<Agent | null> => {
    const fromApi = await safeFetch<Agent | null>(`/agents/${id}`, null);
    if (fromApi) return fromApi;
    return mockAgents.find((agent) => agent.id === id) ?? null;
  },
  getActivity: (): Promise<Activity[]> => safeFetch('/activity', mockActivity),
  getTasks: (): Promise<TaskItem[]> => safeFetch('/tasks', mockTasks),
};
