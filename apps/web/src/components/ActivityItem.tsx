import type { EventItem } from '../types';

interface ActivityItemProps {
  item: EventItem;
}

export function ActivityItem({ item }: ActivityItemProps) {
  const detail = (item.payload?.detail as string) ?? item.event_type;
  return (
    <li className="card" style={{ padding: '10px 14px' }}>
      <div className="row-between">
        <strong style={{ fontSize: '0.9rem' }}>{item.event_type}</strong>
        <small style={{ color: '#6b7280' }}>{item.created_at}</small>
      </div>
      <p style={{ margin: '4px 0 0', fontSize: '0.85rem', color: '#6b7280' }}>{detail}</p>
    </li>
  );
}
