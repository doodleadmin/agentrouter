import type { ApprovalItem } from '../types';
import { ShieldIcon } from './ui/icons';

interface ApprovalsCardProps {
  approvals: ApprovalItem[];
  loading?: boolean;
}

const statusTone: Record<string, string> = {
  pending: '#f59e0b',
  approved: '#16a34a',
  rejected: '#ef4444',
};

export function ApprovalsCard({ approvals, loading }: ApprovalsCardProps) {
  const pendingCount = approvals.filter((a) => a.status === 'pending').length;

  if (loading) {
    return (
      <section className="glass-card">
        <div className="skeleton-stack" aria-hidden="true">
          <div className="skeleton skeleton--title" />
          <div className="skeleton skeleton--line" />
          <div className="skeleton skeleton--line" style={{ width: '78%' }} />
        </div>
      </section>
    );
  }

  if (approvals.length === 0) {
    return (
      <section className="glass-card">
        <ShieldIcon width={20} height={20} style={{ color: 'var(--text-tertiary)', marginBottom: 8 }} />
        <h4 style={{ margin: 0, marginBottom: 4 }}>Approvals</h4>
        <small className="product-card-subtitle">
          No approval requests yet. Dangerous actions (deploy, migrations, environment changes) will appear here for review.
        </small>
      </section>
    );
  }

  return (
    <section className="glass-card">
      <div className="row-between" style={{ marginBottom: 8 }}>
        <h4 style={{ margin: 0 }}>Approvals</h4>
        {pendingCount > 0 && (
          <span className="pill pill-orange">{pendingCount} pending</span>
        )}
      </div>
      <div className="stack" style={{ gap: 6 }}>
        {approvals.slice(0, 5).map((a) => (
          <div key={a.id} className="row-between" style={{ fontSize: '0.85rem' }}>
            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {a.action}
            </span>
            <span
              className="pill"
              style={{
                backgroundColor: statusTone[a.status] ?? 'var(--text-secondary)',
                color: '#fff',
                fontSize: '0.70rem',
                padding: '2px 6px',
              }}
            >
              {a.status.toUpperCase()}
            </span>
          </div>
        ))}
        {approvals.length > 5 && (
          <small className="product-card-subtitle">+{approvals.length - 5} more</small>
        )}
      </div>
    </section>
  );
}
