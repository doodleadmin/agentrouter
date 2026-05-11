interface MetricCardProps {
  value: string | number;
  label: string;
  sublabel?: string;
}

export function MetricCard({ value, label, sublabel }: MetricCardProps) {
  return (
    <div className="metric-card">
      <span className="metric-value">{value}</span>
      <span className="metric-label">{label}</span>
      {sublabel && <span className="metric-sublabel">{sublabel}</span>}
    </div>
  );
}
