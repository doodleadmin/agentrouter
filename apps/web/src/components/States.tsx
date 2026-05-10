/** Reusable states: loading spinner, empty placeholder, error banner. */

export function LoadingState({ message = 'Loading…' }: { message?: string }) {
  return (
    <div className="card" style={{ textAlign: 'center', padding: '24px' }}>
      <div className="spinner" />
      <p style={{ marginTop: 12, color: '#6b7280' }}>{message}</p>
    </div>
  );
}

export function EmptyState({ message = 'No items found' }: { message?: string }) {
  return (
    <div className="card" style={{ textAlign: 'center', padding: '24px' }}>
      <p style={{ color: '#6b7280' }}>{message}</p>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="card" style={{ textAlign: 'center', padding: '24px' }}>
      <p style={{ color: '#dc2626' }}>{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="retry-btn">
          Retry
        </button>
      )}
    </div>
  );
}
