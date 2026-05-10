import type { Agent } from '../types';
import { StatusPill } from './StatusPill';

interface AgentDetailCardProps {
  agent: Agent;
}

export function AgentDetailCard({ agent }: AgentDetailCardProps) {
  const tone = agent.status === 'active' ? 'green' : agent.status === 'idle' ? 'blue' : 'gray';

  return (
    <section className="card">
      <div className="row-between">
        <h2>{agent.name}</h2>
        <StatusPill label={agent.status} tone={tone} />
      </div>
      <p>{agent.role}</p>
      <ul>
        <li>Projects: {agent.projectCount}</li>
        <li>Last activity: {agent.lastActivity}</li>
      </ul>
    </section>
  );
}
