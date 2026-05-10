import { useState } from 'react';
import type { AgentSummary, FormState, TopicKind } from '../../types';
import { TOPIC_KINDS, TOPIC_KIND_LABELS } from '../../types';

interface TopicBindingFormProps {
  agents: AgentSummary[];
  onSubmit: (data: {
    chat_id: number;
    message_thread_id: number;
    title: string;
    kind: TopicKind;
    agent_id: string | null;
  }) => Promise<void>;
  formState: FormState;
}

export function TopicBindingForm({ agents, onSubmit, formState }: TopicBindingFormProps) {
  const [chatId, setChatId] = useState('');
  const [threadId, setThreadId] = useState('');
  const [title, setTitle] = useState('');
  const [kind, setKind] = useState<TopicKind>('general');
  const [agentId, setAgentId] = useState('');

  const requiresAgent = kind === 'agent';

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void onSubmit({
      chat_id: Number(chatId),
      message_thread_id: Number(threadId),
      title,
      kind,
      agent_id: agentId || null,
    });
  };

  const canSubmit =
    formState.status !== 'submitting' &&
    chatId.trim() &&
    threadId.trim() &&
    title.trim() &&
    (!requiresAgent || agentId.trim());

  return (
    <form onSubmit={handleSubmit} className="stack">
      <div className="form-disclaimer">
        This only registers a mapping between a Telegram topic and a backend role.
        It does <strong>not</strong> create a topic in Telegram.
        Create the topic manually in your Telegram group first.
      </div>
      <label className="form-label">
        Chat ID *
        <input
          className="form-input"
          type="number"
          value={chatId}
          onChange={(e) => setChatId(e.target.value)}
          placeholder="e.g. -1001234567890"
          required
        />
      </label>
      <label className="form-label">
        Thread ID *
        <input
          className="form-input"
          type="number"
          value={threadId}
          onChange={(e) => setThreadId(e.target.value)}
          placeholder="e.g. 17"
          required
        />
      </label>
      <label className="form-label">
        Title *
        <input
          className="form-input"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Agent: Backend"
          required
        />
      </label>
      <label className="form-label">
        Kind *
        <select
          className="form-input"
          value={kind}
          onChange={(e) => setKind(e.target.value as TopicKind)}
        >
          {TOPIC_KINDS.map((k) => (
            <option key={k} value={k}>
              {TOPIC_KIND_LABELS[k]}
            </option>
          ))}
        </select>
      </label>
      {requiresAgent && (
        <label className="form-label">
          Agent *
          <select
            className="form-input"
            value={agentId}
            onChange={(e) => setAgentId(e.target.value)}
            required
          >
            <option value="">— select agent —</option>
            {agents.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </label>
      )}
      {formState.status === 'error' && (
        <div className="form-error">{formState.error}</div>
      )}
      {formState.status === 'success' ? (
        <div className="form-success">Topic binding registered!</div>
      ) : (
        <button type="submit" className="form-submit" disabled={!canSubmit}>
          {formState.status === 'submitting' ? 'Registering…' : 'Register Binding'}
        </button>
      )}
    </form>
  );
}
