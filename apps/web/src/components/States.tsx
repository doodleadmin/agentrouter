/** Reusable states: skeleton-first loading, empty placeholder, error banner. */

import type { ReactNode } from 'react';
import { GridIcon } from './ui/icons';

export function LoadingState({ message = 'Loading…' }: { message?: string }) {
  return (
    <div className="glass-card" style={{ padding: '20px' }}>
      <div className="skeleton-stack" aria-hidden="true">
        <div className="skeleton skeleton--title" />
        <div className="skeleton skeleton--line" />
        <div className="skeleton skeleton--line" style={{ width: '82%' }} />
      </div>
      <p className="card-copy card-copy--compact" style={{ marginTop: '14px' }}>{message}</p>
    </div>
  );
}

export function EmptyState({ message = 'No items found', action }: { message?: string; action?: ReactNode }) {
  return (
    <div className="glass-card state-empty">
      <GridIcon className="state-empty__icon" />
      <p className="card-copy">{message}</p>
      {action}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="glass-card" style={{ textAlign: 'center', padding: '32px' }}>
      <p style={{ color: 'var(--danger)', margin: 0, fontWeight: 600 }}>{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="retry-btn">
          Retry
        </button>
      )}
    </div>
  );
}
