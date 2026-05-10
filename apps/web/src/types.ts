/**
 * Type definitions aligned with backend API schemas.
 *
 * Backend responses use UUIDs for IDs and ISO-8601 timestamps.
 * Mock fallback shapes remain compatible for local preview.
 */

/* ── Agent ──────────────────────────────────────────────────────── */

export type AgentStatus = 'active' | 'idle' | 'offline';

/** Matches backend AgentRead schema. */
export interface Agent {
  id: string;
  slug: string;
  name: string;
  role: string;
  system_prompt: string;
  model: string | null;
  permissions: Record<string, unknown>;
  status: string;
  created_at: string;
  updated_at: string;
}

/** Simplified agent for list display (derived from AgentRead). */
export interface AgentSummary {
  id: string;
  slug: string;
  name: string;
  role: string;
  status: string;
  lastActivity: string;
}

/* ── Task ───────────────────────────────────────────────────────── */

export type TaskRisk = 'low' | 'medium' | 'high';
export type TaskStatus =
  | 'created'
  | 'routed'
  | 'planning'
  | 'waiting_approval'
  | 'approved'
  | 'running'
  | 'tests_running'
  | 'pr_created'
  | 'deploying_staging'
  | 'deploying_production'
  | 'completed'
  | 'failed'
  | 'cancelled';

/** Matches backend TaskRead schema. */
export interface TaskItem {
  id: string;
  external_id: string;
  title: string;
  raw_text: string;
  normalized_text: string;
  status: string;
  risk_level: string;
  intent: string | null;
  project_id: string | null;
  agent_id: string | null;
  telegram_chat_id: number | null;
  telegram_thread_id: number | null;
  created_by: number | null;
  branch_name: string | null;
  worktree_path: string | null;
  plan_text: string | null;
  result_summary: string | null;
  payload: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

/** Simplified task for list display. */
export interface TaskSummary {
  id: string;
  external_id: string;
  title: string;
  status: string;
  risk_level: string;
  created_at: string;
}

/* ── Approval ───────────────────────────────────────────────────── */

export interface ApprovalItem {
  id: string;
  task_id: string;
  action: string;
  status: string;
  requested_by_agent_id: string | null;
  approved_by: number | null;
  reason: string | null;
  payload: Record<string, unknown>;
  decided_at: string | null;
  created_at: string;
  updated_at: string;
}

/* ── Event ──────────────────────────────────────────────────────── */

export interface EventItem {
  id: string;
  task_id: string;
  event_type: string;
  actor_type: string;
  actor_id: string | null;
  payload: Record<string, unknown>;
  created_at: string;
}

/* ── System ─────────────────────────────────────────────────────── */

export interface SystemStatus {
  status: string;
  service: string;
  version: string;
  timestamp: string;
  checks: {
    api: string;
    database: string;
    redis: string;
  };
}

/** Derived summary for dashboard cards. */
export interface SystemStatusSummary {
  healthy: boolean;
  database: string;
  redis: string;
  version: string;
}

/* ── Auth ───────────────────────────────────────────────────────── */

export interface AuthResponse {
  user_id: number;
  first_name: string | null;
  last_name: string | null;
  username: string | null;
  auth_date: number;
  hash_summary: string;
  session_token: string;
}

/* ── API state ──────────────────────────────────────────────────── */

export type ApiState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: string };
