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
import { SectionHeader } from '../components/ui/SectionHeader';
import { ChatIcon, GridIcon, RobotIcon, ShieldIcon } from '../components/ui/icons';

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
    live: 'var(--success)',
    mock: 'var(--text-secondary)',
    preview: 'var(--text-secondary)',
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
      <div
        className="page-mode-badge"
        style={{
          backgroundColor: context.isTelegramWebApp ? 'rgba(240, 253, 244, 0.95)' : 'rgba(255, 255, 255, 0.82)',
          color: modeTone[apiMode],
        }}
      >
        <span style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          backgroundColor: modeTone[apiMode],
          display: 'inline-block',
        }} />
        {modeLabel[apiMode] || 'Preview'}
        {context.isTelegramWebApp && ' \u00b7 Telegram'}
        {token && ' \u00b7 Guarded mode'}
      </div>

      {/* System status */}
      {statusState.status === 'loading' && <LoadingState message="Loading system status…" />}
      {statusState.status === 'success' && statusState.data && <StatusCard status={statusState.data} />}
      {statusState.status === 'error' && <div className="glass-card" style={{ color: 'var(--danger)' }}>Status unavailable</div>}

      {/* Product overview cards */}
      <SectionHeader title="Product" />
      <div className="stack list-stagger">
        <article
          className="glass-card glass-card--clickable"
          onClick={() => navigate('/workspaces')}
        >
          <div className="row-between">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <GridIcon width={24} height={24} />
              <div>
                <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 600 }}>Workspaces</h3>
                <small className="product-card-subtitle">Where agents work</small>
              </div>
            </div>
          </div>
        </article>
        <article
          className="glass-card glass-card--clickable"
          onClick={() => navigate('/agents')}
        >
          <div className="row-between">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <RobotIcon width={24} height={24} />
              <div>
                <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 600 }}>Agent Team</h3>
                <small className="product-card-subtitle">{agentCount} registered</small>
              </div>
            </div>
          </div>
        </article>
        <article
          className="glass-card glass-card--clickable"
          onClick={() => navigate('/topics')}
        >
          <div className="row-between">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <ChatIcon width={24} height={24} />
              <div>
                <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 600 }}>Telegram Topics</h3>
                <small className="product-card-subtitle">Agent routing</small>
              </div>
            </div>
          </div>
        </article>
        <article className="glass-card">
          <div className="row-between">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <ShieldIcon width={24} height={24} />
              <div>
                <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 600 }}>Approvals</h3>
                <small className="product-card-subtitle">{pendingApprovalCount} pending</small>
              </div>
            </div>
          </div>
        </article>
      </div>

      {/* Summary metrics */}
      <SectionHeader title="Overview" />
      <section className="glass-card grid-3">
        <div>
          <h3 style={{ margin: 0, fontSize: '1.4rem' }}>{agentCount}</h3>
          <small style={{ color: 'var(--text-secondary)' }}>
            Agent{agentCount !== 1 ? 's' : ''}
            {activeAgentCount > 0 && activeAgentCount < agentCount ? ` (${activeAgentCount} active)` : ''}
          </small>
        </div>
        <div>
          <h3 style={{ margin: 0, fontSize: '1.4rem' }}>{taskCount}</h3>
          <small style={{ color: 'var(--text-secondary)' }}>
            Task{taskCount !== 1 ? 's' : ''}
            {pendingTaskCount > 0 ? ` (${pendingTaskCount} pending)` : ''}
          </small>
        </div>
        <div>
          <h3 style={{ margin: 0, fontSize: '1.4rem' }}>{pendingApprovalCount}</h3>
          <small style={{ color: 'var(--text-secondary)' }}>Pending approvals</small>
        </div>
      </section>

      {/* Quick actions */}
      <SectionHeader title="Quick actions" />
      <div className="stack">
        <article
          className="glass-card glass-card--clickable"
          onClick={() => navigate('/tasks/new')}
        >
          <h3 style={{ margin: 0, marginBottom: 4 }}>Create task</h3>
          <small className="product-card-subtitle">
            Route a new request to agent queue
            {token ? ' — creates a real task record' : ''}
          </small>
        </article>
        <article
          className="glass-card glass-card--clickable"
          onClick={() => navigate('/agents/new')}
        >
          <h3 style={{ margin: 0, marginBottom: 4 }}>Register agent</h3>
          <small className="product-card-subtitle">
            Add a new agent to the system
            {token ? ' — creates a real agent record' : ''}
          </small>
        </article>
      </div>

      {/* Approvals */}
      <SectionHeader title="Approvals" />
      <ApprovalsCard
        approvals={approvalsState.status === 'success' ? approvalsState.data : []}
        loading={approvalsState.status === 'loading'}
      />
      {approvalsState.status === 'error' && (
        <div className="glass-card" style={{ color: 'var(--danger)', fontSize: '0.85rem' }}>
          Failed to load approvals.{' '}
          <button onClick={approvalsState.refetch} className="retry-btn" style={{ marginLeft: 4 }}>Retry</button>
        </div>
      )}

      {/* Active agents */}
      <SectionHeader title="Active agents" />
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
        <div className="glass-card" style={{ color: 'var(--danger)' }}>
          Failed to load agents.
          <button onClick={agentsState.refetch} className="retry-btn" style={{ marginLeft: 8 }}>Retry</button>
        </div>
      )}

      {/* Recent activity */}
      <SectionHeader title="Recent activity" />
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
        <div className="glass-card" style={{ color: 'var(--danger)' }}>
          Failed to load activity.
          <button onClick={activityState.refetch} className="retry-btn" style={{ marginLeft: 8 }}>Retry</button>
        </div>
      )}
    </PageContainer>
  );
}
