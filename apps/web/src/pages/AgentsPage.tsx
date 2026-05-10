import { useNavigate } from 'react-router-dom';
import { api, getSessionToken, useApi } from '../api/client';
import type { AgentSummary } from '../types';
import { AgentListItem } from '../components/AgentListItem';
import { EmptyState, ErrorState, LoadingState } from '../components/States';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';

export function AgentsPage() {
  const navigate = useNavigate();
  const agentsState = useApi<AgentSummary[]>(api.getAgents);
  const token = getSessionToken();

  const activeCount = agentsState.status === 'success'
    ? agentsState.data.filter((a) => a.status !== 'offline').length
    : 0;

  return (
    <PageContainer>
      <Header title="Agents" subtitle={agentsState.status === 'success'
        ? `${agentsState.data.length} registered${activeCount > 0 ? ` (${activeCount} active)` : ''}`
        : 'All registered agents'}
      />
      <button className="form-submit" style={{ marginBottom: 12 }} onClick={() => navigate('/agents/new')}>
        + Register Agent
      </button>

      {agentsState.status === 'loading' && <LoadingState message="Loading agents…" />}
      {agentsState.status === 'error' && <ErrorState message={agentsState.error || 'Failed to load agents'} onRetry={agentsState.refetch} />}
      {agentsState.status === 'success' && agentsState.data.length === 0 && (
        <EmptyState message="No agents registered yet" />
      )}
      {agentsState.status === 'success' && agentsState.data.length > 0 && (
        <div className="stack">
          {agentsState.data.map((agent) => <AgentListItem key={agent.id} agent={agent} />)}
        </div>
      )}

      {token && (
        <div className="form-disclaimer" style={{ marginTop: 16 }}>
          Connected to production API. Registering a new agent will create a real agent record.
        </div>
      )}
    </PageContainer>
  );
}
