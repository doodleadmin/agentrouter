import { useNavigate } from 'react-router-dom';
import type { AgentSummary } from '../types';

interface AgentListItemProps {
  agent: AgentSummary;
}

const statusTone: Record<string, string> = {
  active: 'green',
  idle: 'blue',
  offline: 'gray',
};

export function AgentListItem({ agent }: AgentListItemProps) {
  const navigate = useNavigate();
  const tone = statusTone[agent.status] ?? 'gray';

  return (
    <article className="glass-card glass-card--clickable" onClick={() => navigate(`/agents/${agent.id}`)}>
      <div className="row-between">
        <strong>{agent.name}</strong>
        <span className={`pill pill-${tone}`}>{agent.status}</span>
      </div>
      <p>{agent.role}</p>
      <small style={{ color: 'var(--text-secondary)' }}>Last: {agent.lastActivity}</small>
    </article>
  );
}
