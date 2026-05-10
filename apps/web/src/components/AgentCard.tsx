import { useNavigate } from 'react-router-dom';
import type { AgentSummary } from '../types';

interface AgentCardProps {
  agent: AgentSummary;
}

const statusTone: Record<string, string> = {
  active: 'green',
  idle: 'blue',
  offline: 'gray',
};

export function AgentCard({ agent }: AgentCardProps) {
  const navigate = useNavigate();
  const tone = statusTone[agent.status] ?? 'gray';

  return (
    <article className="card" onClick={() => navigate(`/agents/${agent.id}`)} style={{ cursor: 'pointer' }}>
      <div className="row-between">
        <strong>{agent.name}</strong>
        <span className={`pill pill-${tone}`}>{agent.status}</span>
      </div>
      <p>{agent.role}</p>
    </article>
  );
}
