import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api, getSessionToken } from '../api/client';
import type { AgentSummary, FormState } from '../types';
import { ConfirmSubmitCard } from '../components/ConfirmSubmitCard';
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
  const [pendingData, setPendingData] = useState<{
    title: string;
    raw_text: string;
    normalized_text: string;
    risk_level: string;
    agent_id: string | null;
  } | null>(null);
  const token = getSessionToken();

  useEffect(() => {
    void api.getAgents().then((data) => {
      setAgents(data);
      setAgentsLoaded(true);
    });
  }, []);

  const handleFormSubmit = async (data: {
    title: string;
    raw_text: string;
    normalized_text: string;
    risk_level: string;
    agent_id: string | null;
  }) => {
    setPendingData(data);
  };

  const handleConfirm = async () => {
    if (!pendingData) return;
    setFormState({ status: 'submitting' });
    try {
      await api.createTask({
        title: pendingData.title,
        raw_text: pendingData.raw_text,
        normalized_text: pendingData.normalized_text,
        risk_level: pendingData.risk_level,
        agent_id: pendingData.agent_id,
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

  const handleCancel = () => {
    setPendingData(null);
    setFormState({ status: 'idle' });
  };

  const selectedAgentName = pendingData?.agent_id
    ? agents.find((a) => a.id === pendingData.agent_id)?.name ?? '—'
    : '—';

  return (
    <PageContainer>
      <Header title="Create Task" subtitle="Route a new request to the agent queue" />
      <div className="card">
        {agentsLoaded ? (
          <TaskForm
            agents={agents}
            preselectedAgentId={preselectedAgentId}
            onSubmit={handleFormSubmit}
            formState={pendingData ? { status: 'idle' } : formState}
          />
        ) : (
          <div className="card">Loading agents…</div>
        )}
      </div>

      {pendingData && (
        <ConfirmSubmitCard
          title="Confirm new task"
          items={[
            { label: 'Title', value: pendingData.title },
            { label: 'Risk', value: pendingData.risk_level },
            { label: 'Agent', value: selectedAgentName },
          ]}
          warning={
            token
              ? 'This will create a real task record in production.'
              : 'Preview mode: API is not connected. A mock record will be created.'
          }
          secondaryNote={
            'This will not run the task, start OpenCode, or execute any commands.' +
            (pendingData.risk_level !== 'low'
              ? ` Medium/high-risk tasks require approval before execution.`
              : '')
          }
          confirmLabel="Create Task"
          onConfirm={handleConfirm}
          onCancel={handleCancel}
          submitting={formState.status === 'submitting'}
        />
      )}
    </PageContainer>
  );
}
