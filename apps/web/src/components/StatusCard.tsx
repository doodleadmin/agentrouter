import type { SystemStatusSummary } from '../types';

interface StatusCardProps {
  status: SystemStatusSummary;
}

export function StatusCard({ status }: StatusCardProps) {
  const statusColor = status.healthy ? 'green' : 'orange';
  return (
    <section className="glass-card grid-3">
      <div>
        <h4 style={{ margin: 0 }}>
          <span className={`pill pill-${statusColor}`}>{status.healthy ? 'OK' : 'WARN'}</span>
        </h4>
        <small style={{ color: 'var(--text-secondary)' }}>System</small>
      </div>
      <div>
        <h4 style={{ margin: 0 }}>{status.database === 'ok' ? '✓' : '✗'}</h4>
        <small style={{ color: 'var(--text-secondary)' }}>Database</small>
      </div>
      <div>
        <h4 style={{ margin: 0 }}>{status.redis === 'ok' ? '✓' : '✗'}</h4>
        <small style={{ color: 'var(--text-secondary)' }}>Redis</small>
      </div>
    </section>
  );
}
