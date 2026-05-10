import { useNavigate } from 'react-router-dom';
import { api, getSessionToken, useApi } from '../api/client';
import { getTelegramContext } from '../lib/telegram';
import { useMemo } from 'react';
import type { AgentSummary, ApprovalItem, EventItem, SystemStatusSummary, TaskSummary } from '../types';
import { ActivityItem } from '../components/ActivityItem';
import { AgentCard } from '../components/AgentCard';
import { ApprovalsCard } from '../components/ApprovalsCard';
import { EmptyState, LoadingState } from '../components/States';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';
import { StatusCard } from '../components/StatusCard';

export function HomePage() {
  const navigate = useNavigate();
  const context = useMemo(() => getTelegramContext(), []);
  const token = getSessionToken();

  const statusState = useApi<SystemStatusSummary>(api.getSystemStatus);
  const agentsState = useApi<AgentSummary[]>(api.getAgents);
  const tasksState = useApi<TaskSummary[]>(api.getTasks);
  const approvalsState = useApi<ApprovalItem[]>(api.getApprovals);
  const activityState = useApi<EventItem[]>(api.getEvents);

  // Determine API mode for indicator
  const apiMode = token
    ? (statusState.status === 'success' && statusState.data?.healthy ? 'live' : 'mock')
    : 'preview';

  const modeLabel: Record<string, string> = {
    live: 'Live API',
    mock: 'Preview data',
    preview: 'Preview mode',
  };

  const modeTone: Record<string, string> = {
    live: '#166534',
    mock: '#6b7280',
    preview: '#6b7280',
  };

  const agentCount = (agentsState.status === 'success' ? agentsState.data.length : 0);
  const activeAgentCount = (agentsState.status === 'success'
    ? agentsState.data.filter((a) => a.status !== 'offline').length
    : 0);

  const taskCount = (tasksState.status === 'success' ? tasksState.data.length : 0);
  const pendingTaskCount = (tasksState.status === 'success'
    ? tasksState.data.filter((t) => ['created', 'routed', 'planning', 'waiting_approval'].includes(t.status)).length
    : 0);

  const pendingApprovalCount = (approvalsState.status === 'success'
    ? approvalsState.data.filter((a) => a.status === 'pending').length
    : 0);

  return (
    <PageContainer>
      <Header title="AI Office" subtitle="Mission Control" />

      {/* Mode + guarded indicator */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        marginBottom: 12,
        padding: '6px 10px',
        borderRadius: 8,
        backgroundColor: context.isTelegramWebApp ? '#ecfdf5' : '#f3f4f6',
        fontSize: '0.80rem',
        color: modeTone[apiMode],
        flexWrap: 'wrap',
      }}>
        <span style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          backgroundColor: modeTone[apiMode],
          display: 'inline-block',
        }} />
        {modeLabel[apiMode] || 'Preview'}
        {context.isTelegramWebApp && ' • Telegram'}
        {token && ' • Guarded mode'}
      </div>

      {/* System status */}
      {statusState.status === 'loading' && <div className="card"><span className="spinner" /></div>}
      {statusState.status === 'success' && statusState.data && <StatusCard status={statusState.data} />}
      {statusState.status === 'error' && <div className="card" style={{ color: '#dc2626' }}>Status unavailable</div>}

      {/* Summary cards */}
      <div className="section-title">Overview</div>
      <section className="card grid-3">
        <div>
          <h3 style={{ margin: 0, fontSize: '1.4rem' }}>{agentCount}</h3>
          <small style={{ color: '#6b7280' }}>
            Agent{agentCount !== 1 ? 's' : ''}
            {activeAgentCount > 0 && activeAgentCount < agentCount ? ` (${activeAgentCount} active)` : ''}
          </small>
        </div>
        <div>
          <h3 style={{ margin: 0, fontSize: '1.4rem' }}>{taskCount}</h3>
          <small style={{ color: '#6b7280' }}>
            Task{taskCount !== 1 ? 's' : ''}
            {pendingTaskCount > 0 ? ` (${pendingTaskCount} pending)` : ''}
          </small>
        </div>
        <div>
          <h3 style={{ margin: 0, fontSize: '1.4rem' }}>{pendingApprovalCount}</h3>
          <small style={{ color: '#6b7280' }}>Pending approvals</small>
        </div>
      </section>

      {/* Quick actions */}
      <div className="section-title">Quick actions</div>
      <div className="stack">
        <article
          className="card quick-action"
          style={{ cursor: 'pointer' }}
          onClick={() => navigate('/tasks/new')}
        >
          <h3 style={{ margin: 0, marginBottom: 4 }}>Create task</h3>
          <small style={{ color: '#6b7280' }}>
            Route a new request to agent queue
            {token ? ' — creates a real task record' : ''}
          </small>
        </article>
        <article
          className="card quick-action"
          style={{ cursor: 'pointer' }}
          onClick={() => navigate('/agents/new')}
        >
          <h3 style={{ margin: 0, marginBottom: 4 }}>Register agent</h3>
          <small style={{ color: '#6b7280' }}>
            Add a new agent to the system
            {token ? ' — creates a real agent record' : ''}
          </small>
        </article>
      </div>

      {/* Approvals */}
      <div className="section-title">Approvals</div>
      <ApprovalsCard
        approvals={approvalsState.status === 'success' ? approvalsState.data : []}
        loading={approvalsState.status === 'loading'}
      />
      {approvalsState.status === 'error' && (
        <div className="card" style={{ color: '#dc2626', fontSize: '0.85rem' }}>
          Failed to load approvals.{' '}
          <button onClick={approvalsState.refetch} className="retry-btn" style={{ marginLeft: 4 }}>Retry</button>
        </div>
      )}

      {/* Active agents */}
      <div className="section-title">Active agents</div>
      {agentsState.status === 'loading' && <LoadingState message="Loading agents…" />}
      {agentsState.status === 'success' && agentsState.data.length === 0 && (
        <EmptyState message="No agents registered yet" />
      )}
      {agentsState.status === 'success' && agentsState.data.length > 0 && (
        <div className="stack">
          {agentsState.data.slice(0, 2).map((agent) => <AgentCard key={agent.id} agent={agent} />)}
        </div>
      )}
      {agentsState.status === 'error' && (
        <div className="card" style={{ color: '#dc2626' }}>
          Failed to load agents.
          <button onClick={agentsState.refetch} className="retry-btn" style={{ marginLeft: 8 }}>Retry</button>
        </div>
      )}

      {/* Recent activity */}
      <div className="section-title">Recent activity</div>
      {activityState.status === 'loading' && <LoadingState message="Loading activity…" />}
      {activityState.status === 'success' && activityState.data.length === 0 && (
        <EmptyState message="No recent activity" />
      )}
      {activityState.status === 'success' && activityState.data.length > 0 && (
        <ul className="stack list-reset">
          {activityState.data.map((item) => <ActivityItem key={item.id} item={item} />)}
        </ul>
      )}
      {activityState.status === 'error' && (
        <div className="card" style={{ color: '#dc2626' }}>
          Failed to load activity.
          <button onClick={activityState.refetch} className="retry-btn" style={{ marginLeft: 8 }}>Retry</button>
        </div>
      )}
    </PageContainer>
  );
}
