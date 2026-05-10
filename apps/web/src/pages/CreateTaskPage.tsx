import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../api/client';
import type { AgentSummary, FormState } from '../types';
import { TaskForm } from '../components/forms/TaskForm';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';

export function CreateTaskPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preselectedAgentId = searchParams.get('agent_id');

  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [agentsLoaded, setAgentsLoaded] = useState(false);
  const [formState, setFormState] = useState<FormState>({ status: 'idle' });

  useEffect(() => {
    void api.getAgents().then((data) => {
      setAgents(data);
      setAgentsLoaded(true);
    });
  }, []);

  const handleSubmit = async (data: {
    title: string;
    raw_text: string;
    normalized_text: string;
    risk_level: string;
    agent_id: string | null;
  }) => {
    setFormState({ status: 'submitting' });
    try {
      await api.createTask({
        title: data.title,
        raw_text: data.raw_text,
        normalized_text: data.normalized_text,
        risk_level: data.risk_level,
        agent_id: data.agent_id,
      });
      setFormState({ status: 'success' });
      setTimeout(() => navigate('/tasks'), 1200);
    } catch (err) {
      setFormState({
        status: 'error',
        error: err instanceof Error ? err.message : 'Failed to create task',
      });
    }
  };

  return (
    <PageContainer>
      <Header title="Create Task" subtitle="Route a new request to the agent queue" />
      <div className="card">
        {agentsLoaded ? (
          <TaskForm
            agents={agents}
            preselectedAgentId={preselectedAgentId}
            onSubmit={handleSubmit}
            formState={formState}
          />
        ) : (
          <div className="card">Loading agents…</div>
        )}
      </div>
    </PageContainer>
  );
}
