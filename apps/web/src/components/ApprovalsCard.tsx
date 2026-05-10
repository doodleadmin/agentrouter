import type { ApprovalItem } from '../types';

interface ApprovalsCardProps {
  approvals: ApprovalItem[];
  loading?: boolean;
}

const statusTone: Record<string, string> = {
  pending: '#f59e0b',
  approved: '#166534',
  rejected: '#dc2626',
};

export function ApprovalsCard({ approvals, loading }: ApprovalsCardProps) {
  const pendingCount = approvals.filter((a) => a.status === 'pending').length;

  if (loading) {
    return (
      <section className="card">
        <div className="spinner" style={{ margin: '12px auto' }} />
      </section>
    );
  }

  if (approvals.length === 0) {
    return (
      <section className="card">
        <h4 style={{ margin: 0, marginBottom: 4 }}>Approvals</h4>
        <small style={{ color: '#6b7280' }}>
          No approval requests yet. Dangerous actions (deploy, migrations, environment changes) will appear here for review.
        </small>
      </section>
    );
  }

  return (
    <section className="card">
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
                backgroundColor: statusTone[a.status] ?? '#6b7280',
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
          <small style={{ color: '#6b7280' }}>+{approvals.length - 5} more</small>
        )}
      </div>
    </section>
  );
}
