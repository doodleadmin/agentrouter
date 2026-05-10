import { useState } from 'react';
import type { AgentSummary, FormState } from '../../types';

interface TaskFormProps {
  agents: AgentSummary[];
  preselectedAgentId?: string | null;
  onSubmit: (data: {
    title: string;
    raw_text: string;
    normalized_text: string;
    risk_level: string;
    agent_id: string | null;
  }) => Promise<void>;
  formState: FormState;
}

export function TaskForm({ agents, preselectedAgentId, onSubmit, formState }: TaskFormProps) {
  const [title, setTitle] = useState('');
  const [rawText, setRawText] = useState('');
  const [riskLevel, setRiskLevel] = useState('low');
  const [agentId, setAgentId] = useState(preselectedAgentId ?? '');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void onSubmit({
      title,
      raw_text: rawText,
      normalized_text: rawText,
      risk_level: riskLevel,
      agent_id: agentId || null,
    });
  };

  const canSubmit = formState.status !== 'submitting' && title.trim() && rawText.trim();

  return (
    <form onSubmit={handleSubmit} className="stack">
      <label className="form-label">
        Title *
        <input
          className="form-input"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Add healthcheck endpoint"
          required
        />
      </label>
      <label className="form-label">
        Description *
        <textarea
          className="form-input form-textarea"
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
          placeholder="Describe the task in detail..."
          rows={4}
          required
        />
      </label>
      <label className="form-label">
        Risk level
        <select
          className="form-input"
          value={riskLevel}
          onChange={(e) => setRiskLevel(e.target.value)}
        >
          <option value="low">Low — read, analyze, plan</option>
          <option value="medium">Medium — code changes, tests</option>
          <option value="high">High — migrations, env, deploy</option>
        </select>
      </label>
      <label className="form-label">
        Assign to agent
        <select
          className="form-input"
          value={agentId}
          onChange={(e) => setAgentId(e.target.value)}
        >
          <option value="">— select agent —</option>
          {agents.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name} ({a.status})
            </option>
          ))}
        </select>
      </label>
      {formState.status === 'error' && (
        <div className="form-error">{formState.error}</div>
      )}
      {formState.status === 'success' ? (
        <div className="form-success">Task created successfully!</div>
      ) : (
        <button type="submit" className="form-submit" disabled={!canSubmit}>
          {formState.status === 'submitting' ? 'Creating…' : 'Create Task'}
        </button>
      )}
    </form>
  );
}
