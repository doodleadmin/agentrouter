interface QuickActionCardProps {
  title: string;
  caption: string;
}

export function QuickActionCard({ title, caption }: QuickActionCardProps) {
  return (
    <article className="card quick-action">
      <h3>{title}</h3>
      <p>{caption}</p>
    </article>
  );
}
