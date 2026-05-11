import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';
import { GlassCard } from '../components/ui/GlassCard';
import { SectionHeader } from '../components/ui/SectionHeader';

type WorkspaceSource = 'local_runner' | 'cloud' | 'github';
type SourceStatus = 'not_connected' | 'coming_soon';

interface WorkspaceSourceCardData {
  id: WorkspaceSource;
  title: string;
  description: string;
  safetyNote?: string;
  status: SourceStatus;
  cta: string;
  icon: string;
}

const WORKSPACE_SOURCES: WorkspaceSourceCardData[] = [
  {
    id: 'local_runner',
    title: 'Local Runner',
    description: 'Work with projects on your own computer. Agents will only access folders inside the allowed root.',
    safetyNote: 'Local file access requires a local runner app. The browser cannot directly access your folders.',
    status: 'not_connected',
    cta: 'Connect Local Runner',
    icon: '💻',
  },
  {
    id: 'cloud',
    title: 'Cloud Workspace',
    description: 'Create isolated online workspaces for agent-generated projects. Download as ZIP or connect GitHub.',
    status: 'coming_soon',
    cta: 'Create Cloud Workspace',
    icon: '☁️',
  },
  {
    id: 'github',
    title: 'GitHub Repository',
    description: 'Connect a repository for reviewed agent changes.',
    status: 'coming_soon',
    cta: 'Connect GitHub',
    icon: '📦',
  },
];

export function WorkspacesPage() {
  return (
    <PageContainer>
      <Header title="Workspaces" subtitle="Choose where agents work" />

      <SectionHeader title="Workspace source" />

      {/* Empty state */}
      <GlassCard>
        <div style={{ textAlign: 'center', padding: '8px 0' }}>
          <p style={{ color: 'var(--text-secondary)', margin: 0, fontSize: '15px' }}>
            No active workspace yet.
          </p>
          <p style={{ color: 'var(--text-tertiary)', margin: '4px 0 0', fontSize: '13px' }}>
            Choose where agents should work: local folder, cloud workspace, or GitHub.
          </p>
        </div>
      </GlassCard>

      {/* Source cards */}
      <div className="stack">
        {WORKSPACE_SOURCES.map((source) => (
          <GlassCard key={source.id}>
            <div className="row-between" style={{ marginBottom: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 28 }}>{source.icon}</span>
                <div>
                  <h3 style={{ margin: 0, fontSize: '17px', fontWeight: 600 }}>{source.title}</h3>
                </div>
              </div>
              <span className={`pill pill-${source.status === 'coming_soon' ? 'gray' : 'blue'}`}>
                {source.status === 'coming_soon' ? 'Coming soon' : 'Not connected'}
              </span>
            </div>
            <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '14px', lineHeight: 1.5 }}>
              {source.description}
            </p>
            {source.safetyNote && (
              <div className="form-disclaimer" style={{ marginTop: 12 }}>
                {source.safetyNote}
              </div>
            )}
            <button
              className="liquid-button liquid-button--secondary"
              style={{ marginTop: 12 }}
              disabled={true}
            >
              {source.cta}
            </button>
          </GlassCard>
        ))}
      </div>

      {/* How it works */}
      <SectionHeader title="How workspaces work" />
      <GlassCard>
        <ol style={{ margin: 0, paddingLeft: 20, color: 'var(--text-secondary)', fontSize: '14px', lineHeight: 1.8 }}>
          <li>Choose a workspace source above</li>
          <li>Create or select an agent team</li>
          <li>Connect your Telegram group with topics</li>
          <li>Assign one agent per topic</li>
          <li>Send tasks via Telegram topics</li>
        </ol>
      </GlassCard>
    </PageContainer>
  );
}
