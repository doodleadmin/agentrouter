import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { Activity, Agent, SystemStatus } from '../types';
import { ActivityItem } from '../components/ActivityItem';
import { AgentCard } from '../components/AgentCard';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';
import { QuickActionCard } from '../components/QuickActionCard';
import { StatusCard } from '../components/StatusCard';

export function HomePage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [activity, setActivity] = useState<Activity[]>([]);

  useEffect(() => {
    void Promise.all([api.getSystemStatus(), api.getAgents(), api.getActivity()]).then(([s, a, act]) => {
      setStatus(s);
      setAgents(a.slice(0, 2));
      setActivity(act);
    });
  }, []);

  return (
    <PageContainer>
      <Header title="Mission Control" subtitle="Overview" />
      {status ? <StatusCard status={status} /> : null}
      <div className="section-title">Quick actions</div>
      <div className="stack">
        <QuickActionCard title="Create task" caption="Route a new request to agent queue" />
        <QuickActionCard title="Approvals" caption="Review pending high-risk actions" />
      </div>
      <div className="section-title">Active agents</div>
      <div className="stack">{agents.map((agent) => <AgentCard key={agent.id} agent={agent} />)}</div>
      <div className="section-title">Recent activity</div>
      <ul className="stack list-reset">{activity.map((item) => <ActivityItem key={item.id} item={item} />)}</ul>
    </PageContainer>
  );
}
