import type { ComponentType, SVGProps } from 'react';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';
import { GlassCard } from '../components/ui/GlassCard';
import { CloudIcon, CodeIcon, FolderIcon, PackageIcon } from '../components/ui/icons';
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
  icon: ComponentType<SVGProps<SVGSVGElement>>;
}

const WORKSPACE_SOURCES: WorkspaceSourceCardData[] = [
  {
    id: 'local_runner',
    title: 'Local Runner',
    description: 'Work with projects on your own computer. Example allowed root: F:\\dev. Access is limited to the selected root.',
    safetyNote: 'Requires local runner app. Browser/Mini App cannot access folders directly. File edits and commands require approvals.',
    status: 'not_connected',
    cta: 'Connect Local Runner',
    icon: CodeIcon,
  },
  {
    id: 'cloud',
    title: 'Cloud Workspace',
    description: 'Create isolated online workspaces for agent-generated projects. Download as ZIP or connect GitHub.',
    status: 'coming_soon',
    cta: 'Create Cloud Workspace',
    icon: CloudIcon,
  },
  {
    id: 'github',
    title: 'GitHub Repository',
    description: 'Connect a repository for reviewed agent changes.',
    status: 'coming_soon',
    cta: 'Connect GitHub',
    icon: PackageIcon,
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
          <FolderIcon width={26} height={26} style={{ color: 'var(--text-tertiary)', marginBottom: 8 }} />
          <p className="card-copy" style={{ marginBottom: 0 }}>
            No active workspace yet.
          </p>
          <p className="card-copy card-copy--compact" style={{ marginTop: 4 }}>
            Choose where agents should work: local folder, cloud workspace, or GitHub.
          </p>
        </div>
      </GlassCard>

      {/* Source cards */}
      <div className="stack list-stagger">
        {WORKSPACE_SOURCES.map((source) => (
          <GlassCard key={source.id}>
            <div className="row-between" style={{ marginBottom: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <source.icon width={28} height={28} />
                <div>
                  <h3 style={{ margin: 0, fontSize: '17px', fontWeight: 600 }}>{source.title}</h3>
                </div>
              </div>
              <span className={`pill pill-${source.status === 'coming_soon' ? 'gray' : 'blue'}`}>
                {source.status === 'coming_soon' ? 'Coming soon' : 'Not connected'}
              </span>
            </div>
            <p className="card-copy">{source.description}</p>
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
        <ol className="support-list">
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
