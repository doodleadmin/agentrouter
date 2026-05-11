/** Reusable states: loading spinner, empty placeholder, error banner. */

export function LoadingState({ message = 'Loading…' }: { message?: string }) {
  return (
    <div className="glass-card" style={{ textAlign: 'center', padding: '32px' }}>
      <div className="spinner" />
      <p style={{ color: 'var(--text-secondary)', margin: '16px 0 0' }}>{message}</p>
    </div>
  );
}

export function EmptyState({ message = 'No items found' }: { message?: string }) {
  return (
    <div className="glass-card" style={{ textAlign: 'center', padding: '32px' }}>
      <p style={{ color: 'var(--text-secondary)' }}>{message}</p>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="glass-card" style={{ textAlign: 'center', padding: '32px' }}>
      <p style={{ color: 'var(--danger)' }}>{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="retry-btn">
          Retry
        </button>
      )}
    </div>
  );
}
