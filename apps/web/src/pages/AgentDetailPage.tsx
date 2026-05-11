import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/client';
import type { Agent } from '../types';
import { AgentDetailCard } from '../components/AgentDetailCard';
import { EmptyState } from '../components/States';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';

export function AgentDetailPage() {
  const { id = '' } = useParams();
  const navigate = useNavigate();
  const [state, setState] = useState<'loading' | 'success' | 'error' | 'empty'>('loading');
  const [agent, setAgent] = useState<Agent | null>(null);

  useEffect(() => {
    let cancelled = false;
    setState('loading');
    void api.getAgentById(id).then((result) => {
      if (cancelled) return;
      if (result) {
        setAgent(result);
        setState('success');
      } else {
        setState('empty');
      }
    }).catch(() => {
      if (!cancelled) setState('error');
    });
    return () => { cancelled = true; };
  }, [id]);

  return (
    <PageContainer>
      <Header title="Agent details" subtitle={id} />
      {state === 'loading' && <div className="glass-card">Loading agent…</div>}
      {state === 'error' && (
        <div className="glass-card" style={{ color: 'var(--danger)' }}>Failed to load agent details</div>
      )}
      {state === 'empty' && <EmptyState message="Agent not found" />}
      {state === 'success' && agent && (
        <>
          <AgentDetailCard agent={agent} />
          <button
            className="liquid-button liquid-button--primary"
            style={{ marginTop: 12 }}
            onClick={() => navigate(`/tasks/new?agent_id=${agent.id}`)}
          >
            Create task for this agent
          </button>
        </>
      )}
    </PageContainer>
  );
}
