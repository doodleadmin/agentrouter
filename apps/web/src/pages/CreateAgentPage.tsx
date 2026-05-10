import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, getSessionToken } from '../api/client';
import type { FormState } from '../types';
import { AgentForm } from '../components/forms/AgentForm';
import { ConfirmSubmitCard } from '../components/ConfirmSubmitCard';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';

export function CreateAgentPage() {
  const navigate = useNavigate();
  const [formState, setFormState] = useState<FormState>({ status: 'idle' });
  const [pendingData, setPendingData] = useState<{
    slug: string;
    name: string;
    role: string;
    system_prompt: string;
    model: string;
  } | null>(null);
  const token = getSessionToken();

  const handleFormSubmit = async (data: {
    slug: string;
    name: string;
    role: string;
    system_prompt: string;
    model: string;
  }) => {
    // First step: show confirmation
    setPendingData(data);
  };

  const handleConfirm = async () => {
    if (!pendingData) return;
    setFormState({ status: 'submitting' });
    try {
      await api.createAgent({
        slug: pendingData.slug || pendingData.name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''),
        name: pendingData.name,
        role: pendingData.role,
        system_prompt: pendingData.system_prompt || `You are ${pendingData.name}. Role: ${pendingData.role}`,
        model: pendingData.model || null,
        status: 'active',
      });
      setFormState({ status: 'success' });
      setTimeout(() => navigate('/agents'), 1200);
    } catch (err) {
      setFormState({
        status: 'error',
        error: err instanceof Error ? err.message : 'Failed to create agent',
      });
    }
  };

  const handleCancel = () => {
    setPendingData(null);
    setFormState({ status: 'idle' });
  };

  return (
    <PageContainer>
      <Header title="Create Agent" subtitle="Register a new agent" />
      <div className="card">
        <AgentForm onSubmit={handleFormSubmit} formState={pendingData ? { status: 'idle' } : formState} />
      </div>

      {pendingData && (
        <ConfirmSubmitCard
          title="Confirm new agent"
          items={[
            { label: 'Name', value: pendingData.name },
            { label: 'Role', value: pendingData.role },
            { label: 'Slug', value: pendingData.slug || pendingData.name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '') },
            { label: 'Model', value: pendingData.model || '—' },
          ]}
          warning={
            token
              ? 'This will create a real agent record in production.'
              : 'Preview mode: API is not connected. A mock record will be created.'
          }
          secondaryNote="This will not start OpenCode or execute any commands."
          confirmLabel="Create Agent"
          onConfirm={handleConfirm}
          onCancel={handleCancel}
          submitting={formState.status === 'submitting'}
        />
      )}
    </PageContainer>
  );
}
