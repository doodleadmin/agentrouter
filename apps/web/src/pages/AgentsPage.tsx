import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { Agent } from '../types';
import { AgentListItem } from '../components/AgentListItem';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';

export function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);

  useEffect(() => {
    void api.getAgents().then(setAgents);
  }, []);

  return (
    <PageContainer>
      <Header title="Agents" subtitle="All registered agents" />
      <div className="stack">{agents.map((agent) => <AgentListItem key={agent.id} agent={agent} />)}</div>
    </PageContainer>
  );
}
