import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client';
import type { Agent } from '../types';
import { AgentDetailCard } from '../components/AgentDetailCard';
import { EmptyState } from '../components/States';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';

export function AgentDetailPage() {
  const { id = '' } = useParams();
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
      {state === 'loading' && <div className="card">Loading agent…</div>}
      {state === 'error' && (
        <div className="card" style={{ color: '#dc2626' }}>Failed to load agent details</div>
      )}
      {state === 'empty' && <EmptyState message="Agent not found" />}
      {state === 'success' && agent && <AgentDetailCard agent={agent} />}
    </PageContainer>
  );
}
