import { useEffect, useState } from 'react';
import { api, getSessionToken, useApi } from '../api/client';
import type { AgentSummary, FormState, TelegramTopicRead } from '../types';
import {
  TOPIC_KIND_LABELS,
  TOPIC_KIND_DESCRIPTIONS,
  TOPIC_KINDS,
} from '../types';
import { TopicBindingForm } from '../components/forms/TopicBindingForm';
import { TopicMappingCard } from '../components/TopicMappingCard';
import { EmptyState, ErrorState, LoadingState } from '../components/States';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';

export function TopicsPage() {
  const topicsState = useApi<TelegramTopicRead[]>(api.getTelegramTopics);
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [formState, setFormState] = useState<FormState>({ status: 'idle' });
  const [showForm, setShowForm] = useState(false);
  const token = getSessionToken();

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

      {/* Role explanation */}
      <div className="section-title">Topic roles</div>
      <div className="stack">
        {TOPIC_KINDS.map((kind) => (
          <article className="card" key={kind}>
            <div className="row-between">
              <strong>{TOPIC_KIND_LABELS[kind]}</strong>
              <span className="pill pill-blue">{kind}</span>
            </div>
            <small style={{ color: '#6b7280', display: 'block', marginTop: 4 }}>
              {TOPIC_KIND_DESCRIPTIONS[kind]}
            </small>
          </article>
        ))}
      </div>

      {/* Existing mappings */}
      <div className="section-title" style={{ marginTop: 20 }}>Registered mappings</div>
      {topicsState.status === 'loading' && <LoadingState message="Loading topics…" />}
      {topicsState.status === 'error' && <ErrorState message="Failed to load topics" onRetry={topicsState.refetch} />}
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

      {/* Registration form */}
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

      {token && (
        <div className="form-disclaimer" style={{ marginTop: 16 }}>
          Connected to production API. Registering a topic binding will create a real mapping record.
        </div>
      )}
    </PageContainer>
  );
}
