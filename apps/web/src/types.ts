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

/* ── Telegram Topic ─────────────────────────────────────────────── */

export const TOPIC_KINDS = ['general', 'agent', 'approvals', 'system_logs', 'task'] as const;
export type TopicKind = (typeof TOPIC_KINDS)[number];

export const TOPIC_KIND_LABELS: Record<TopicKind, string> = {
  general: 'General / Orchestrator',
  agent: 'Agent',
  approvals: 'Approvals',
  system_logs: 'System Logs',
  task: 'Task Thread',
};

export const TOPIC_KIND_DESCRIPTIONS: Record<TopicKind, string> = {
  general: 'Default chat, system messages, coordination',
  agent: 'Bound to a specific agent for direct communication',
  approvals: 'Approval flow notifications and decisions',
  system_logs: 'Infrastructure, deploy, and error logs',
  task: 'Per-task conversation thread',
};

/** Matches backend TelegramTopicRead. */
export interface TelegramTopicRead {
  id: string;
  chat_id: number;
  message_thread_id: number;
  title: string;
  kind: string;
  agent_id: string | null;
  project_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/* ── Create payloads ────────────────────────────────────────────── */

/** Matches backend AgentCreate. */
export interface AgentCreatePayload {
  slug: string;
  name: string;
  role: string;
  system_prompt: string;
  model?: string | null;
  permissions?: Record<string, unknown>;
  status?: string;
}

/** Matches backend TaskCreate. */
export interface TaskCreatePayload {
  title: string;
  raw_text: string;
  normalized_text: string;
  risk_level?: string;
  intent?: string | null;
  project_id?: string | null;
  agent_id?: string | null;
  telegram_chat_id?: number | null;
  telegram_thread_id?: number | null;
  created_by?: number | null;
}

/** Matches backend TelegramTopicCreate. */
export interface TelegramTopicCreatePayload {
  chat_id: number;
  message_thread_id: number;
  title: string;
  kind: TopicKind;
  agent_id?: string | null;
  project_id?: string | null;
  is_active?: boolean;
}

/* ── API state ──────────────────────────────────────────────────── */

export type ApiState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: string };

/** Form submission state. */
export type FormState =
  | { status: 'idle' }
  | { status: 'submitting' }
  | { status: 'success' }
  | { status: 'error'; error: string };

/* ── Workspace (foundation) ────────────────────────────────────── */

export type WorkspaceSourceType = 'local_runner' | 'cloud' | 'github';
export type WorkspaceSourceStatus = 'not_connected' | 'connected' | 'coming_soon';

export interface WorkspaceSourceCard {
  id: WorkspaceSourceType;
  title: string;
  description: string;
  safetyNote?: string;
  status: WorkspaceSourceStatus;
  cta: string;
  icon: string;
}

/* ── Local Runner (protocol design, non-executing) ─────────────── */

export type RunnerStatus = 'not_connected' | 'pairing' | 'online' | 'offline' | 'suspended' | 'revoked' | 'error';

export type RunnerConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error';

export type RunnerSafetyMode = 'read_only' | 'approval_gated' | 'execution_disabled';

export type RunnerOperationKind =
  | 'read_file'
  | 'search_files'
  | 'list_tree'
  | 'propose_patch'
  | 'apply_patch'
  | 'create_file'
  | 'rename_file'
  | 'delete_file'
  | 'propose_command'
  | 'run_command';

export type RunnerApprovalClass =
  | 'read_safe'
  | 'read_sensitive'
  | 'write_file'
  | 'delete_file'
  | 'run_command'
  | 'network_access'
  | 'git_commit'
  | 'git_push'
  | 'dependency_install'
  | 'env_access'
  | 'destructive_action';

export interface RunnerCapability {
  name: 'read_tree' | 'read_file' | 'search' | 'propose_patch' | 'apply_patch' | 'propose_command' | 'run_command';
  enabled: boolean;
  approval_required: boolean;
}

export interface WorkspaceProject {
  name: string;
  relative_path: string;
  last_modified?: string;
}
