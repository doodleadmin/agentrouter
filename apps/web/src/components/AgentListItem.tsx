import { Link } from 'react-router-dom';
import type { Agent } from '../types';
import { StatusPill } from './StatusPill';

interface AgentListItemProps {
  agent: Agent;
}

export function AgentListItem({ agent }: AgentListItemProps) {
  const tone = agent.status === 'active' ? 'green' : agent.status === 'idle' ? 'blue' : 'gray';

  return (
    <Link to={`/agents/${agent.id}`} className="card list-link">
      <div className="row-between">
        <div>
          <strong>{agent.name}</strong>
          <p>{agent.role}</p>
        </div>
        <StatusPill label={agent.status} tone={tone} />
      </div>
    </Link>
  );
}
