/** Reusable confirmation card for production create flows. */

interface ConfirmSubmitCardProps {
  title: string;
  items: { label: string; value: string }[];
  warning?: string;
  secondaryNote?: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  submitting?: boolean;
}

export function ConfirmSubmitCard({
  title,
  items,
  warning,
  secondaryNote,
  confirmLabel = 'Confirm',
  onConfirm,
  onCancel,
  submitting = false,
}: ConfirmSubmitCardProps) {
  return (
    <div className="glass-card" style={{ marginTop: 12 }}>
      <h3 style={{ margin: 0, marginBottom: 10 }}>{title}</h3>
      <div className="stack" style={{ gap: 6, marginBottom: 12 }}>
        {items.map((item) => (
          <div key={item.label} className="row-between">
            <small style={{ color: 'var(--text-secondary)' }}>{item.label}</small>
            <strong style={{ fontSize: '0.88rem', textAlign: 'right' }}>{item.value}</strong>
          </div>
        ))}
      </div>
      {warning && (
        <div className="form-disclaimer" style={{ marginBottom: 8 }}>
          {warning}
        </div>
      )}
      {secondaryNote && (
        <small style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: 10, fontSize: '0.80rem' }}>
          {secondaryNote}
        </small>
      )}
      <div className="row-between" style={{ gap: 8 }}>
        <button
          type="button"
          className="liquid-button liquid-button--ghost"
          style={{ flex: 1, marginTop: 0 }}
          onClick={onCancel}
          disabled={submitting}
        >
          Cancel
        </button>
        <button
          type="button"
          className="liquid-button liquid-button--primary"
          style={{ flex: 1, marginTop: 0 }}
          onClick={onConfirm}
          disabled={submitting}
        >
          {submitting ? 'Sending…' : confirmLabel}
        </button>
      </div>
    </div>
  );
}
