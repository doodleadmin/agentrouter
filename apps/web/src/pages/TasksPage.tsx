import { useNavigate } from 'react-router-dom';
import { api, useApi } from '../api/client';
import type { TaskSummary } from '../types';
import { EmptyState } from '../components/States';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';
import { StatusPill } from '../components/StatusPill';

const statusTone: Record<string, 'green' | 'orange' | 'blue' | 'gray'> = {
  running: 'green',
  tests_running: 'green',
  waiting_approval: 'orange',
  approved: 'green',
  created: 'blue',
  routed: 'blue',
  planning: 'blue',
  completed: 'green',
  failed: 'gray',
  cancelled: 'gray',
};

const riskTone: Record<string, 'green' | 'orange' | 'gray'> = {
  low: 'green',
  medium: 'orange',
  high: 'gray',
};

export function TasksPage() {
  const navigate = useNavigate();
  const tasksState = useApi<TaskSummary[]>(api.getTasks);

  return (
    <PageContainer>
      <Header title="Tasks" subtitle="Queue and execution status" />
      <button className="form-submit" style={{ marginBottom: 12 }} onClick={() => navigate('/tasks/new')}>
        + Create Task
      </button>
      {tasksState.status === 'loading' && <div className="card">Loading tasks…</div>}
      {tasksState.status === 'error' && (
        <div className="card" style={{ color: '#dc2626' }}>
          Failed to load tasks. {tasksState.error}
          <br />
          <button onClick={tasksState.refetch} className="retry-btn">Retry</button>
        </div>
      )}
      {tasksState.status === 'success' && tasksState.data.length === 0 && (
        <EmptyState message="No tasks in the queue" />
      )}
      {tasksState.status === 'success' && tasksState.data.length > 0 && (
        <div className="stack">
          {tasksState.data.map((task) => (
            <article className="card" key={task.id}>
              <div className="row-between">
                <strong>{task.external_id}</strong>
                <div style={{ display: 'flex', gap: 4 }}>
                  <StatusPill label={task.risk_level} tone={riskTone[task.risk_level] ?? 'gray'} />
                  <StatusPill label={task.status} tone={statusTone[task.status] ?? 'blue'} />
                </div>
              </div>
              <p>{task.title}</p>
              <small style={{ color: '#6b7280' }}>
                {new Date(task.created_at).toLocaleString()}
              </small>
            </article>
          ))}
        </div>
      )}
    </PageContainer>
  );
}
