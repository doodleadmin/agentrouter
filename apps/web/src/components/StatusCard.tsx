import type { SystemStatus } from '../types';

interface StatusCardProps {
  status: SystemStatus;
}

export function StatusCard({ status }: StatusCardProps) {
  return (
    <section className="card grid-3">
      <div>
        <h3>{status.onlineAgents}</h3>
        <p>Online agents</p>
      </div>
      <div>
        <h3>{status.queuedTasks}</h3>
        <p>Queued tasks</p>
      </div>
      <div>
        <h3>{status.approvalsPending}</h3>
        <p>Approvals</p>
      </div>
    </section>
  );
}
