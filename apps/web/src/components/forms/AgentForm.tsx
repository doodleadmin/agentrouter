import { useState } from 'react';
import type { FormState } from '../../types';

interface AgentFormProps {
  onSubmit: (data: { slug: string; name: string; role: string; system_prompt: string; model: string }) => Promise<void>;
  formState: FormState;
}

export function AgentForm({ onSubmit, formState }: AgentFormProps) {
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [role, setRole] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [model, setModel] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void onSubmit({
      slug: slug || name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''),
      name,
      role,
      system_prompt: systemPrompt,
      model,
    });
  };

  const canSubmit = formState.status !== 'submitting' && name.trim() && role.trim();

  return (
    <form onSubmit={handleSubmit} className="stack">
      <label className="form-label">
        Name *
        <input
          className="form-input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Backend Architect"
          required
        />
      </label>
      <label className="form-label">
        Slug
        <input
          className="form-input"
          value={slug}
          onChange={(e) => setSlug(e.target.value)}
          placeholder="auto-generated from name"
        />
      </label>
      <label className="form-label">
        Role *
        <input
          className="form-input"
          value={role}
          onChange={(e) => setRole(e.target.value)}
          placeholder="e.g. FastAPI / DB / Services"
          required
        />
      </label>
      <label className="form-label">
        System prompt
        <textarea
          className="form-input form-textarea"
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          placeholder="Instructions for the agent..."
          rows={4}
        />
      </label>
      <label className="form-label">
        Model
        <input
          className="form-input"
          value={model}
          onChange={(e) => setModel(e.target.value)}
          placeholder="optional, e.g. gpt-4o"
        />
      </label>
      {formState.status === 'error' && (
        <div className="form-error">{formState.error}</div>
      )}
      {formState.status === 'success' ? (
        <div className="form-success">Agent created successfully!</div>
      ) : (
        <button type="submit" className="form-submit" disabled={!canSubmit}>
          {formState.status === 'submitting' ? 'Creating…' : 'Create Agent'}
        </button>
      )}
    </form>
  );
}
