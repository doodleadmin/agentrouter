import type { Agent } from '../types';

interface AgentDetailCardProps {
  agent: Agent;
}

export function AgentDetailCard({ agent }: AgentDetailCardProps) {
  return (
    <div className="stack">
      <section className="card">
        <div className="row-between">
          <h3>{agent.name}</h3>
          <span className="pill pill-green">{agent.status}</span>
        </div>
        <p><strong>Slug:</strong> {agent.slug}</p>
        <p><strong>Role:</strong> {agent.role}</p>
        {agent.model && <p><strong>Model:</strong> {agent.model}</p>}
      </section>
      <section className="card">
        <h3>Permissions</h3>
        <pre style={{ fontSize: '0.8rem', overflow: 'auto', margin: 0 }}>
          {JSON.stringify(agent.permissions, null, 2)}
        </pre>
      </section>
      <section className="card">
        <p style={{ fontSize: '0.82rem', color: '#6b7280' }}>
          Created: {new Date(agent.created_at).toLocaleString()}
        </p>
        <p style={{ fontSize: '0.82rem', color: '#6b7280' }}>
          Updated: {new Date(agent.updated_at).toLocaleString()}
        </p>
      </section>
    </div>
  );
}
