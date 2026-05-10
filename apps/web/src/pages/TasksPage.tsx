import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { TaskItem } from '../types';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';
import { StatusPill } from '../components/StatusPill';

export function TasksPage() {
  const [tasks, setTasks] = useState<TaskItem[]>([]);

  useEffect(() => {
    void api.getTasks().then(setTasks);
  }, []);

  return (
    <PageContainer>
      <Header title="Tasks" subtitle="Queue and execution status" />
      <div className="stack">
        {tasks.map((task) => (
          <article className="card" key={task.id}>
            <div className="row-between">
              <strong>{task.id}</strong>
              <StatusPill
                label={task.status}
                tone={task.status === 'running' ? 'green' : task.status === 'waiting_approval' ? 'orange' : 'blue'}
              />
            </div>
            <p>{task.title}</p>
          </article>
        ))}
      </div>
    </PageContainer>
  );
}
