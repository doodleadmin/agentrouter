import type { SystemStatusSummary } from '../types';
import { CheckCircleIcon, XCircleIcon } from './ui/icons';

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
        <small className="product-card-subtitle">System</small>
      </div>
      <div>
        <h4 style={{ margin: 0 }}>
          {status.database === 'ok' ? <CheckCircleIcon width={18} height={18} /> : <XCircleIcon width={18} height={18} />}
        </h4>
        <small className="product-card-subtitle">Database</small>
      </div>
      <div>
        <h4 style={{ margin: 0 }}>
          {status.redis === 'ok' ? <CheckCircleIcon width={18} height={18} /> : <XCircleIcon width={18} height={18} />}
        </h4>
        <small className="product-card-subtitle">Redis</small>
      </div>
    </section>
  );
}
