interface StatusPillProps {
  label: string;
  tone?: 'green' | 'blue' | 'orange' | 'gray';
}

export function StatusPill({ label, tone = 'gray' }: StatusPillProps) {
  return <span className={`pill pill-${tone}`}>{label}</span>;
}
