/**
 * API client — connects to real backend when available, falls back to mocks.
 *
 * Real endpoints (proxied through Vite dev server):
 *   /api/agents          → GET list
 *   /api/agents/:id      → GET single
 *   /api/tasks           → GET list (with query params)
 *   /api/approvals       → GET list
 *   /api/events          → GET list
 *   /api/health          → GET system status
 *   /api/telegram/webapp/auth → POST auth
 */

import { mockActivity, mockAgentSummaries, mockSystemStatus, mockTaskSummaries } from './mockData';
import type {
  Agent,
  ApiState,
  ApprovalItem,
  AuthResponse,
  EventItem,
  SystemStatus,
  SystemStatusSummary,
  TaskItem,
  TaskSummary,
} from '../types';

const API_BASE = '/api';

// ── Session management ──────────────────────────────────────────────

let _sessionToken: string | null = null;

export function getSessionToken(): string | null {
  return _sessionToken;
}

export function setSessionToken(token: string | null): void {
  _sessionToken = token;
}

// ── Generic fetch with auth ──────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (_sessionToken) {
    headers['Authorization'] = `Bearer ${_sessionToken}`;
  }

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!response.ok) {
    throw new Error(`API ${response.status}: ${response.statusText}`);
  }
  return (await response.json()) as T;
}

// ── Safe fetch with mock fallback ────────────────────────────────────

async function safeFetch<T>(path: string, fallback: T): Promise<T> {
  try {
    return await apiFetch<T>(path);
  } catch {
    return fallback;
  }
}

// ── Transformers: backend → UI shapes ────────────────────────────────

function agentToSummary(a: Agent): import('../types').AgentSummary {
  return {
    id: a.id,
    slug: a.slug,
    name: a.name,
    role: a.role,
    status: a.status,
    lastActivity: new Date(a.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  };
}

function taskToSummary(t: TaskItem): TaskSummary {
  return {
    id: t.id,
    external_id: t.external_id,
    title: t.title,
    status: t.status,
    risk_level: t.risk_level,
    created_at: t.created_at,
  };
}

function statusToSummary(s: SystemStatus): SystemStatusSummary {
  return {
    healthy: s.status === 'ok',
    database: s.checks.database,
    redis: s.checks.redis,
    version: s.version,
  };
}

// ── Public API ───────────────────────────────────────────────────────

export const api = {
  // Auth
  authenticate: async (initData: string): Promise<AuthResponse> => {
    const resp = await fetch(`${API_BASE}/telegram/webapp/auth`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ initData }),
    });
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(text);
    }
    const data = (await resp.json()) as AuthResponse;
    _sessionToken = data.session_token;
    return data;
  },

  // System
  getSystemStatus: (): Promise<SystemStatusSummary> =>
    safeFetch<SystemStatus>('/health', mockSystemStatus).then(statusToSummary),

  // Agents
  getAgents: (): Promise<import('../types').AgentSummary[]> =>
    safeFetch<Agent[]>('/agents?active_only=true', []).then((agents) =>
      agents.length > 0 ? agents.map(agentToSummary) : mockAgentSummaries
    ),

  getAgentById: async (id: string): Promise<Agent | null> => {
    const fromApi = await safeFetch<Agent | null>(`/agents/${id}`, null);
    return fromApi;
  },

  // Tasks
  getTasks: (): Promise<TaskSummary[]> =>
    safeFetch<TaskItem[]>('/tasks?limit=20', []).then((tasks) =>
      tasks.length > 0 ? tasks.map(taskToSummary) : mockTaskSummaries
    ),

  // Approvals
  getApprovals: (): Promise<ApprovalItem[]> =>
    safeFetch<ApprovalItem[]>('/approvals', []),

  // Events
  getEvents: (limit = 10): Promise<EventItem[]> =>
    safeFetch<EventItem[]>(`/events?limit=${limit}`, mockActivity as unknown as EventItem[]),
};

// ── Hook helper: useApi ──────────────────────────────────────────────

import { useCallback, useEffect, useState } from 'react';

/** Reactive wrapper for API calls with loading/error/empty state. */
export function useApi<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = [],
): ApiState<T> & { refetch: () => void } {
  const [state, setState] = useState<ApiState<T>>({ status: 'idle' });

  const load = useCallback(async () => {
    setState({ status: 'loading' });
    try {
      const data = await fetcher();
      setState({ status: 'success', data });
    } catch (err) {
      setState({ status: 'error', error: err instanceof Error ? err.message : 'Unknown error' });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    void load();
  }, [load]);

  return { ...state, refetch: load };
}
