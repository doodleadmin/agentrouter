import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client';
import type { Agent } from '../types';
import { AgentDetailCard } from '../components/AgentDetailCard';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';

export function AgentDetailPage() {
  const { id = '' } = useParams();
  const [agent, setAgent] = useState<Agent | null>(null);

  useEffect(() => {
    void api.getAgentById(id).then(setAgent);
  }, [id]);

  return (
    <PageContainer>
      <Header title="Agent details" subtitle={id} />
      {agent ? <AgentDetailCard agent={agent} /> : <div className="card">Agent not found</div>}
    </PageContainer>
  );
}
