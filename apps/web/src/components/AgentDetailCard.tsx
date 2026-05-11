import type { Agent } from '../types';

interface AgentDetailCardProps {
  agent: Agent;
}

export function AgentDetailCard({ agent }: AgentDetailCardProps) {
  return (
    <div className="stack">
      <section className="glass-card">
        <div className="row-between">
          <h3>{agent.name}</h3>
          <span className="pill pill-green">{agent.status}</span>
        </div>
        <p><strong>Slug:</strong> {agent.slug}</p>
        <p><strong>Role:</strong> {agent.role}</p>
        {agent.model && <p><strong>Model:</strong> {agent.model}</p>}
      </section>
      <section className="glass-card">
        <h3>Permissions</h3>
        <pre style={{ fontSize: '0.8rem', overflow: 'auto', margin: 0 }}>
          {JSON.stringify(agent.permissions, null, 2)}
        </pre>
      </section>
      <section className="glass-card">
        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
          Created: {new Date(agent.created_at).toLocaleString()}
        </p>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
          Updated: {new Date(agent.updated_at).toLocaleString()}
        </p>
      </section>
    </div>
  );
}
