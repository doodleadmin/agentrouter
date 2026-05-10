import { api, useApi } from '../api/client';
import type { AgentSummary, EventItem, SystemStatusSummary } from '../types';
import { ActivityItem } from '../components/ActivityItem';
import { AgentCard } from '../components/AgentCard';
import { EmptyState } from '../components/States';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';
import { QuickActionCard } from '../components/QuickActionCard';
import { StatusCard } from '../components/StatusCard';

export function HomePage() {
  const statusState = useApi<SystemStatusSummary>(api.getSystemStatus);
  const agentsState = useApi<AgentSummary[]>(api.getAgents);
  const activityState = useApi<EventItem[]>(api.getEvents);

  return (
    <PageContainer>
      <Header title="Mission Control" subtitle="Overview" />

      {/* System status */}
      {statusState.status === 'loading' && <div className="card">Loading status…</div>}
      {statusState.status === 'success' && statusState.data && <StatusCard status={statusState.data} />}
      {statusState.status === 'error' && <div className="card">Status unavailable</div>}

      {/* Quick actions */}
      <div className="section-title">Quick actions</div>
      <div className="stack">
        <QuickActionCard title="Create task" caption="Route a new request to agent queue" />
        <QuickActionCard title="Approvals" caption="Review pending high-risk actions" />
      </div>

      {/* Active agents */}
      <div className="section-title">Active agents</div>
      {agentsState.status === 'loading' && <div className="card">Loading agents…</div>}
      {agentsState.status === 'success' && agentsState.data.length === 0 && (
        <EmptyState message="No active agents" />
      )}
      {agentsState.status === 'success' && agentsState.data.length > 0 && (
        <div className="stack">
          {agentsState.data.slice(0, 2).map((agent) => <AgentCard key={agent.id} agent={agent} />)}
        </div>
      )}
      {agentsState.status === 'error' && <div className="card">Failed to load agents</div>}

      {/* Recent activity */}
      <div className="section-title">Recent activity</div>
      {activityState.status === 'loading' && <div className="card">Loading activity…</div>}
      {activityState.status === 'success' && activityState.data.length === 0 && (
        <EmptyState message="No recent activity" />
      )}
      {activityState.status === 'success' && activityState.data.length > 0 && (
        <ul className="stack list-reset">
          {activityState.data.map((item) => <ActivityItem key={item.id} item={item} />)}
        </ul>
      )}
      {activityState.status === 'error' && <div className="card">Failed to load activity</div>}
    </PageContainer>
  );
}
