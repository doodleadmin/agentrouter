import { useEffect, useState } from 'react';
import { api, useApi } from '../api/client';
import type { AgentSummary, FormState, TelegramTopicRead } from '../types';
import { TopicBindingForm } from '../components/forms/TopicBindingForm';
import { TopicMappingCard } from '../components/TopicMappingCard';
import { EmptyState } from '../components/States';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';

export function TopicsPage() {
  const topicsState = useApi<TelegramTopicRead[]>(api.getTelegramTopics);
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [formState, setFormState] = useState<FormState>({ status: 'idle' });
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    void api.getAgents().then(setAgents);
  }, []);

  const handleBindingSubmit = async (data: {
    chat_id: number;
    message_thread_id: number;
    title: string;
    kind: string;
    agent_id: string | null;
  }) => {
    setFormState({ status: 'submitting' });
    try {
      await api.createTelegramTopic({
        chat_id: data.chat_id,
        message_thread_id: data.message_thread_id,
        title: data.title,
        kind: data.kind as 'general' | 'agent' | 'approvals' | 'system_logs' | 'task',
        agent_id: data.agent_id,
      });
      setFormState({ status: 'success' });
      setTimeout(() => {
        setShowForm(false);
        setFormState({ status: 'idle' });
        topicsState.refetch();
      }, 1200);
    } catch (err) {
      setFormState({
        status: 'error',
        error: err instanceof Error ? err.message : 'Failed to register binding',
      });
    }
  };

  return (
    <PageContainer>
      <Header title="Topic Bindings" subtitle="Telegram topic ↔ role mappings" />

      {/* Existing mappings */}
      <div className="section-title">Registered mappings</div>
      {topicsState.status === 'loading' && <div className="card">Loading topics…</div>}
      {topicsState.status === 'error' && (
        <div className="card" style={{ color: '#dc2626' }}>
          Failed to load topics.
          <br />
          <button onClick={topicsState.refetch} className="retry-btn">Retry</button>
        </div>
      )}
      {topicsState.status === 'success' && topicsState.data.length === 0 && (
        <EmptyState message="No topic bindings registered yet" />
      )}
      {topicsState.status === 'success' && topicsState.data.length > 0 && (
        <div className="stack">
          {topicsState.data.map((topic) => (
            <TopicMappingCard key={topic.id} topic={topic} />
          ))}
        </div>
      )}

      {/* Registration form toggle */}
      <div className="section-title">Register new binding</div>
      {!showForm ? (
        <button className="form-submit" onClick={() => setShowForm(true)}>
          + Register Topic Binding
        </button>
      ) : (
        <div className="card">
          <TopicBindingForm
            agents={agents}
            onSubmit={handleBindingSubmit}
            formState={formState}
          />
          {formState.status !== 'success' && (
            <button
              className="retry-btn"
              style={{ marginTop: 8 }}
              onClick={() => { setShowForm(false); setFormState({ status: 'idle' }); }}
            >
              Cancel
            </button>
          )}
        </div>
      )}
    </PageContainer>
  );
}
