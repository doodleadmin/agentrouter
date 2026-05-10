import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import type { FormState } from '../types';
import { AgentForm } from '../components/forms/AgentForm';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';

export function CreateAgentPage() {
  const navigate = useNavigate();
  const [formState, setFormState] = useState<FormState>({ status: 'idle' });

  const handleSubmit = async (data: {
    slug: string;
    name: string;
    role: string;
    system_prompt: string;
    model: string;
  }) => {
    setFormState({ status: 'submitting' });
    try {
      await api.createAgent({
        slug: data.slug,
        name: data.name,
        role: data.role,
        system_prompt: data.system_prompt || `You are ${data.name}. Role: ${data.role}`,
        model: data.model || null,
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

  return (
    <PageContainer>
      <Header title="Create Agent" subtitle="Register a new agent" />
      <div className="card">
        <AgentForm onSubmit={handleSubmit} formState={formState} />
      </div>
    </PageContainer>
  );
}
