export function SectionHeader({ title, action }: { title: string; action?: React.ReactNode }) {
  return (
    <div className="section-header-row">
      <h2 className="section-header">{title}</h2>
      {action}
    </div>
  );
}
