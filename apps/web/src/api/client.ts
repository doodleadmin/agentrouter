/**
 * API client — connects to real backend when available, falls back to mocks.
 *
 * Real endpoints (proxied through Vite dev server):
 *   /api/agents          → GET list, POST create
 *   /api/agents/:id      → GET single
 *   /api/tasks           → GET list (with query params), POST create
 *   /api/approvals       → GET list
 *   /api/events          → GET list
 *   /api/health          → GET system status
 *   /api/telegram/webapp/auth → POST auth
 *   /api/telegram/topics → GET list, POST create
 */

import { mockActivity, mockAgentSummaries, mockSystemStatus, mockTaskSummaries, mockTopics } from './mockData';
import type {
  Agent,
  AgentCreatePayload,
  ApiState,
  ApprovalItem,
  AuthResponse,
  EventItem,
  SystemStatus,
  SystemStatusSummary,
  TaskCreatePayload,
  TaskItem,
  TaskSummary,
  TelegramTopicCreatePayload,
  TelegramTopicRead,
} from '../types';

// API base URL. In production under /app/, API is at same origin.
// In local dev, Vite proxy or direct connection.
// VITE_API_BASE_URL can override for custom setups.
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

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

  createAgent: async (payload: AgentCreatePayload): Promise<Agent> => {
    try {
      return await apiFetch<Agent>('/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    } catch {
      // Mock fallback: return simulated created agent
      return {
        id: crypto.randomUUID(),
        slug: payload.slug,
        name: payload.name,
        role: payload.role,
        system_prompt: payload.system_prompt,
        model: payload.model ?? null,
        permissions: payload.permissions ?? {},
        status: payload.status ?? 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
    }
  },

  // Tasks
  getTasks: (): Promise<TaskSummary[]> =>
    safeFetch<TaskItem[]>('/tasks?limit=20', []).then((tasks) =>
      tasks.length > 0 ? tasks.map(taskToSummary) : mockTaskSummaries
    ),

  createTask: async (payload: TaskCreatePayload): Promise<TaskItem> => {
    try {
      return await apiFetch<TaskItem>('/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    } catch {
      // Mock fallback: return simulated created task
      return {
        id: crypto.randomUUID(),
        external_id: `task-${String(Date.now()).slice(-6)}`,
        title: payload.title,
        raw_text: payload.raw_text,
        normalized_text: payload.normalized_text,
        status: 'created',
        risk_level: payload.risk_level ?? 'low',
        intent: payload.intent ?? null,
        project_id: payload.project_id ?? null,
        agent_id: payload.agent_id ?? null,
        telegram_chat_id: payload.telegram_chat_id ?? null,
        telegram_thread_id: payload.telegram_thread_id ?? null,
        created_by: payload.created_by ?? null,
        branch_name: null,
        worktree_path: null,
        plan_text: null,
        result_summary: null,
        payload: {},
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
    }
  },

  // Approvals
  getApprovals: (): Promise<ApprovalItem[]> =>
    safeFetch<ApprovalItem[]>('/approvals', []),

  // Events
  getEvents: (limit = 10): Promise<EventItem[]> =>
    safeFetch<EventItem[]>(`/events?limit=${limit}`, mockActivity as unknown as EventItem[]),

  // Telegram Topics
  getTelegramTopics: (): Promise<TelegramTopicRead[]> =>
    safeFetch<TelegramTopicRead[]>('/telegram/topics?active_only=false', mockTopics),

  createTelegramTopic: async (payload: TelegramTopicCreatePayload): Promise<TelegramTopicRead> => {
    try {
      return await apiFetch<TelegramTopicRead>('/telegram/topics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    } catch {
      // Mock fallback: return simulated created topic
      return {
        id: crypto.randomUUID(),
        chat_id: payload.chat_id,
        message_thread_id: payload.message_thread_id,
        title: payload.title,
        kind: payload.kind,
        agent_id: payload.agent_id ?? null,
        project_id: payload.project_id ?? null,
        is_active: payload.is_active ?? true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
    }
  },
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
