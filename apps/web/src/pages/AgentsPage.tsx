import { useNavigate } from 'react-router-dom';
import { api, getSessionToken, useApi } from '../api/client';
import type { AgentSummary } from '../types';
import { AgentListItem } from '../components/AgentListItem';
import { EmptyState, ErrorState, LoadingState } from '../components/States';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';
import { SectionHeader } from '../components/ui/SectionHeader';

const AGENT_TEMPLATES = [
  { role: 'Orchestrator', desc: 'Coordinates tasks across agents, routes messages, manages workflow', icon: '🎯' },
  { role: 'Frontend Developer', desc: 'React, TypeScript, UI components, styling, API integration', icon: '🎨' },
  { role: 'Backend Developer', desc: 'FastAPI, databases, API endpoints, services, workers', icon: '⚙️' },
  { role: 'DevOps Engineer', desc: 'Docker, CI/CD, deployment, monitoring, infrastructure', icon: '🔧' },
  { role: 'QA Engineer', desc: 'Testing, verification, consistency review, edge cases', icon: '🧪' },
  { role: 'Designer', desc: 'UI/UX design, design tokens, component specs, accessibility', icon: '✨' },
  { role: 'Product Manager', desc: 'Requirements, priorities, roadmap, user stories', icon: '📋' },
  { role: 'Code Reviewer', desc: 'PR review, code quality, standards enforcement, security audit', icon: '🔍' },
];

export function AgentsPage() {
  const navigate = useNavigate();
  const agentsState = useApi<AgentSummary[]>(api.getAgents);
  const token = getSessionToken();

  const activeCount = agentsState.status === 'success'
    ? agentsState.data.filter((a) => a.status !== 'offline').length
    : 0;

  return (
    <PageContainer>
      <Header title="Agents" subtitle={agentsState.status === 'success'
        ? `${agentsState.data.length} registered${activeCount > 0 ? ` (${activeCount} active)` : ''}`
        : 'All registered agents'}
      />
      <button className="liquid-button liquid-button--primary" style={{ marginBottom: 12 }} onClick={() => navigate('/agents/new')}>
        + Register Agent
      </button>

      {agentsState.status === 'loading' && <LoadingState message="Loading agents…" />}
      {agentsState.status === 'error' && <ErrorState message={agentsState.error || 'Failed to load agents'} onRetry={agentsState.refetch} />}
      {agentsState.status === 'success' && agentsState.data.length === 0 && (
        <EmptyState message="No agents registered yet" />
      )}
      {agentsState.status === 'success' && agentsState.data.length > 0 && (
        <div className="stack">
          {agentsState.data.map((agent) => <AgentListItem key={agent.id} agent={agent} />)}
        </div>
      )}

      {/* Agent Templates */}
      <SectionHeader title="Agent templates" />
      <div className="stack">
        {AGENT_TEMPLATES.map((tmpl) => (
          <article
            key={tmpl.role}
            className="glass-card glass-card--clickable"
            onClick={() => navigate('/agents/new')}
          >
            <div className="row-between">
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 24 }}>{tmpl.icon}</span>
                <div>
                  <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 600 }}>{tmpl.role}</h3>
                  <small style={{ color: 'var(--text-secondary)' }}>{tmpl.desc}</small>
                </div>
              </div>
            </div>
          </article>
        ))}
      </div>

      {token && (
        <div className="form-disclaimer" style={{ marginTop: 16 }}>
          Connected to production API. Registering a new agent will create a real agent record.
        </div>
      )}
    </PageContainer>
  );
}
