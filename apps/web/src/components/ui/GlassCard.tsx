interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  style?: React.CSSProperties;
}

export function GlassCard({ children, className = '', onClick, style }: GlassCardProps) {
  return (
    <div
      className={`glass-card ${onClick ? 'glass-card--clickable' : ''} ${className}`}
      onClick={onClick}
      style={style}
    >
      {children}
    </div>
  );
}
