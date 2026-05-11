import { useEffect, useState } from 'react';
import { api, getSessionToken, useApi } from '../api/client';
import type { AgentSummary, FormState, TelegramTopicRead } from '../types';
import {
  TOPIC_KIND_LABELS,
  TOPIC_KIND_DESCRIPTIONS,
  TOPIC_KINDS,
} from '../types';
import { ConfirmSubmitCard } from '../components/ConfirmSubmitCard';
import { TopicBindingForm } from '../components/forms/TopicBindingForm';
import { TopicMappingCard } from '../components/TopicMappingCard';
import { EmptyState, ErrorState, LoadingState } from '../components/States';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';
import { SectionHeader } from '../components/ui/SectionHeader';

export function TopicsPage() {
  const topicsState = useApi<TelegramTopicRead[]>(api.getTelegramTopics);
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [formState, setFormState] = useState<FormState>({ status: 'idle' });
  const [showForm, setShowForm] = useState(false);
  const [pendingData, setPendingData] = useState<{
    chat_id: number;
    message_thread_id: number;
    title: string;
    kind: string;
    agent_id: string | null;
  } | null>(null);
  const token = getSessionToken();

  useEffect(() => {
    void api.getAgents().then(setAgents);
  }, []);

  const handleFormSubmit = async (data: {
    chat_id: number;
    message_thread_id: number;
    title: string;
    kind: string;
    agent_id: string | null;
  }) => {
    setPendingData(data);
  };

  const handleConfirm = async () => {
    if (!pendingData) return;
    setFormState({ status: 'submitting' });
    try {
      await api.createTelegramTopic({
        chat_id: pendingData.chat_id,
        message_thread_id: pendingData.message_thread_id,
        title: pendingData.title,
        kind: pendingData.kind as 'general' | 'agent' | 'approvals' | 'system_logs' | 'task',
        agent_id: pendingData.agent_id,
      });
      setFormState({ status: 'success' });
      setTimeout(() => {
        setShowForm(false);
        setPendingData(null);
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

  const handleCancel = () => {
    setPendingData(null);
    setFormState({ status: 'idle' });
  };

  const pendingKindLabel = pendingData
    ? TOPIC_KIND_LABELS[pendingData.kind as keyof typeof TOPIC_KIND_LABELS] ?? pendingData.kind
    : '';

  return (
    <PageContainer>
      <Header title="Topic Bindings" subtitle="Telegram topic \u2194 role mappings" />

      {/* Setup guide */}
      <SectionHeader title="Setup guide" />
      <div className="glass-card">
        <ol className="setup-guide">
          <li>Create a Telegram group and enable Topics</li>
          <li>Create a &quot;General&quot; topic for orchestrator input</li>
          <li>Create one topic per agent</li>
          <li>Register each topic binding here</li>
        </ol>
      </div>

      {/* Role explanation */}
      <SectionHeader title="Topic roles" />
      <div className="stack">
        {TOPIC_KINDS.map((kind) => (
          <article className="glass-card" key={kind}>
            <div className="row-between">
              <strong>{TOPIC_KIND_LABELS[kind]}</strong>
              <span className="pill pill-blue">{kind}</span>
            </div>
            <small style={{ color: 'var(--text-secondary)', display: 'block', marginTop: 4 }}>
              {TOPIC_KIND_DESCRIPTIONS[kind]}
            </small>
          </article>
        ))}
      </div>

      {/* Existing mappings */}
      <SectionHeader title="Registered mappings" />
      {topicsState.status === 'loading' && <LoadingState message="Loading topics…" />}
      {topicsState.status === 'error' && <ErrorState message="Failed to load topics" onRetry={topicsState.refetch} />}
      {topicsState.status === 'success' && topicsState.data.length === 0 && (
        <EmptyState message="No topic bindings yet. Create a topic manually in your Telegram Forum group first, then register the mapping here." />
      )}
      {topicsState.status === 'success' && topicsState.data.length > 0 && (
        <div className="stack">
          {topicsState.data.map((topic) => (
            <TopicMappingCard key={topic.id} topic={topic} />
          ))}
        </div>
      )}

      {/* Registration form */}
      <SectionHeader title="Register new binding" />
      {!showForm ? (
        <button className="liquid-button liquid-button--primary" onClick={() => setShowForm(true)}>
          + Register Topic Binding
        </button>
      ) : (
        <div className="glass-card">
          <TopicBindingForm
            agents={agents}
            onSubmit={handleFormSubmit}
            formState={pendingData ? { status: 'idle' } : formState}
          />
          {formState.status !== 'success' && !pendingData && (
            <button
              className="liquid-button liquid-button--ghost"
              style={{ marginTop: 8 }}
              onClick={() => { setShowForm(false); setFormState({ status: 'idle' }); }}
            >
              Cancel
            </button>
          )}
        </div>
      )}

      {pendingData && (
        <ConfirmSubmitCard
          title="Confirm topic binding"
          items={[
            { label: 'Chat ID', value: String(pendingData.chat_id) },
            { label: 'Thread ID', value: String(pendingData.message_thread_id) },
            { label: 'Title', value: pendingData.title },
            { label: 'Kind', value: pendingKindLabel },
            { label: 'Agent', value: pendingData.agent_id ? agents.find((a) => a.id === pendingData.agent_id)?.name ?? '\u2014' : '\u2014' },
          ]}
          warning={
            token
              ? 'This will create a real topic mapping record in production. It will NOT create a Telegram topic.'
              : 'Preview mode: API is not connected. A mock record will be created. It does NOT create a Telegram topic.'
          }
          secondaryNote="Create the topic manually in Telegram first, then register the mapping here."
          confirmLabel="Register Binding"
          onConfirm={handleConfirm}
          onCancel={handleCancel}
          submitting={formState.status === 'submitting'}
        />
      )}

      {token && (
        <div className="form-disclaimer" style={{ marginTop: 16 }}>
          Connected to production API. Registering a topic binding will create a real mapping record.
        </div>
      )}
    </PageContainer>
  );
}
