import type { SystemStatusSummary } from '../types';

interface StatusCardProps {
  status: SystemStatusSummary;
}

export function StatusCard({ status }: StatusCardProps) {
  const statusColor = status.healthy ? 'green' : 'orange';
  return (
    <section className="card grid-3">
      <div>
        <h3>
          <span className={`pill pill-${statusColor}`}>{status.healthy ? 'OK' : 'WARN'}</span>
        </h3>
        <p>System</p>
      </div>
      <div>
        <h3>{status.database === 'ok' ? '✓' : '✗'}</h3>
        <p>Database</p>
      </div>
      <div>
        <h3>{status.redis === 'ok' ? '✓' : '✗'}</h3>
        <p>Redis</p>
      </div>
    </section>
  );
}
