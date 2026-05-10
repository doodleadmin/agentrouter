import { api, useApi } from '../api/client';
import type { AgentSummary } from '../types';
import { AgentListItem } from '../components/AgentListItem';
import { EmptyState } from '../components/States';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';

export function AgentsPage() {
  const agentsState = useApi<AgentSummary[]>(api.getAgents);

  return (
    <PageContainer>
      <Header title="Agents" subtitle="All registered agents" />
      {agentsState.status === 'loading' && <div className="card">Loading agents…</div>}
      {agentsState.status === 'error' && (
        <div className="card" style={{ color: '#dc2626' }}>
          Failed to load agents. {agentsState.error}
          <br />
          <button onClick={agentsState.refetch} className="retry-btn">Retry</button>
        </div>
      )}
      {agentsState.status === 'success' && agentsState.data.length === 0 && (
        <EmptyState message="No agents registered yet" />
      )}
      {agentsState.status === 'success' && agentsState.data.length > 0 && (
        <div className="stack">
          {agentsState.data.map((agent) => <AgentListItem key={agent.id} agent={agent} />)}
        </div>
      )}
    </PageContainer>
  );
}
