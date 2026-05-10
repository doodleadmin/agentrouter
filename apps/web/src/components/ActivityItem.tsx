import type { Activity } from '../types';

interface ActivityItemProps {
  item: Activity;
}

export function ActivityItem({ item }: ActivityItemProps) {
  return (
    <li className="card activity-item">
      <div className="row-between">
        <strong>{item.title}</strong>
        <small>{item.time}</small>
      </div>
      <p>{item.detail}</p>
    </li>
  );
}
