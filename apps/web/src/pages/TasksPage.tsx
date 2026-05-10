import { useNavigate } from 'react-router-dom';
import { api, getSessionToken, useApi } from '../api/client';
import type { TaskSummary } from '../types';
import { EmptyState, ErrorState, LoadingState } from '../components/States';
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
  const token = getSessionToken();

  const taskCount = tasksState.status === 'success' ? tasksState.data.length : 0;
  const pendingCount = tasksState.status === 'success'
    ? tasksState.data.filter((t) => ['created', 'routed', 'planning', 'waiting_approval'].includes(t.status)).length
    : 0;

  return (
    <PageContainer>
      <Header
        title="Tasks"
        subtitle={taskCount > 0
          ? `${taskCount} task${taskCount !== 1 ? 's' : ''}${pendingCount > 0 ? ` (${pendingCount} pending)` : ''}`
          : 'Queue and execution status'}
      />
      <button className="form-submit" style={{ marginBottom: 12 }} onClick={() => navigate('/tasks/new')}>
        + Create Task
      </button>

      {tasksState.status === 'loading' && <LoadingState message="Loading tasks…" />}
      {tasksState.status === 'error' && <ErrorState message={tasksState.error || 'Failed to load tasks'} onRetry={tasksState.refetch} />}
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
              <p style={{ margin: '6px 0' }}>{task.title}</p>
              <small style={{ color: '#6b7280' }}>
                {new Date(task.created_at).toLocaleString()}
              </small>
            </article>
          ))}
        </div>
      )}

      {token && (
        <div className="form-disclaimer" style={{ marginTop: 16 }}>
          Connected to production API. Creating a new task will create a real task record.
          Tasks in production will go through the normal review and approval flow.
        </div>
      )}
    </PageContainer>
  );
}
