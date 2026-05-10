import type { Agent } from '../types';
import { StatusPill } from './StatusPill';

interface AgentCardProps {
  agent: Agent;
}

export function AgentCard({ agent }: AgentCardProps) {
  const tone = agent.status === 'active' ? 'green' : agent.status === 'idle' ? 'blue' : 'gray';

  return (
    <article className="card">
      <div className="row-between">
        <h3>{agent.name}</h3>
        <StatusPill label={agent.status} tone={tone} />
      </div>
      <p>{agent.role}</p>
      <small>
        {agent.projectCount} projects · last activity {agent.lastActivity}
      </small>
    </article>
  );
}
