import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import type { SystemStatusSummary } from '../types';
import { getTelegramContext } from '../lib/telegram';
import { getSessionToken } from '../api/client';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';
import { SectionHeader } from '../components/ui/SectionHeader';

type AuthStatus = 'preview' | 'pending' | 'verified' | 'failed' | 'unavailable';
type SessionStatus = 'active' | 'unavailable';
type ApiMode = 'live' | 'mock' | 'preview' | 'error';

export function MorePage() {
  const navigate = useNavigate();
  const context = useMemo(() => getTelegramContext(), []);
  const token = getSessionToken();
  const [systemStatus, setSystemStatus] = useState<SystemStatusSummary | null>(null);
  const [apiMode, setApiMode] = useState<ApiMode>('preview');

  useEffect(() => {
    void api.getSystemStatus().then((s) => {
      setSystemStatus(s);
      if (token) {
        setApiMode(s.healthy ? 'live' : 'error');
      } else {
        setApiMode('mock');
      }
    }).catch(() => {
      setApiMode('error');
    });
  }, [token]);

  // Derive safe statuses — never show raw token/initData values
  const authStatus: AuthStatus = useMemo(() => {
    if (!context.isTelegramWebApp) return 'preview';
    if (!token) return 'unavailable';
    return 'verified';
  }, [context.isTelegramWebApp, token]);

  const sessionStatus: SessionStatus = token ? 'active' : 'unavailable';

  const authStatusLabel: Record<AuthStatus, string> = {
    preview: 'Preview mode: opened outside Telegram',
    pending: 'Auth pending\u2026',
    verified: 'Telegram session verified',
    failed: 'Auth failed, retry',
    unavailable: 'Auth unavailable',
  };

  const authStatusTone: Record<AuthStatus, string> = {
    preview: 'var(--text-secondary)',
    pending: 'var(--warning)',
    verified: 'var(--success)',
    failed: 'var(--danger)',
    unavailable: 'var(--text-secondary)',
  };

  const apiModeLabel: Record<ApiMode, string> = {
    live: 'Live API',
    mock: 'Preview data',
    preview: 'Preview mode',
    error: 'API unavailable',
  };

  const apiModeTone: Record<ApiMode, string> = {
    live: 'var(--success)',
    mock: 'var(--text-secondary)',
    preview: 'var(--text-secondary)',
    error: 'var(--danger)',
  };

  return (
    <PageContainer>
      <Header title="More" subtitle="Settings &amp; diagnostics" />

      {/* Auth & Session */}
      <SectionHeader title="Authentication" />
      <section className="glass-card">
        <div className="row-between">
          <div>
            <h4 style={{ margin: 0 }}>Telegram WebApp</h4>
            <small style={{ color: 'var(--text-secondary)' }}>
              {context.isTelegramWebApp ? 'Detected' : 'Not detected (browser preview)'}
            </small>
          </div>
          <span className={`pill pill-${context.isTelegramWebApp ? 'green' : 'gray'}`}>
            {context.isTelegramWebApp ? 'ON' : 'OFF'}
          </span>
        </div>
      </section>

      <section className="glass-card">
        <div className="row-between">
          <div>
            <h4 style={{ margin: 0 }}>Auth status</h4>
            <small style={{ color: authStatusTone[authStatus] }}>{authStatusLabel[authStatus]}</small>
          </div>
          <span
            className="pill"
            style={{ backgroundColor: authStatusTone[authStatus], color: '#fff' }}
          >
            {authStatus.toUpperCase()}
          </span>
        </div>
      </section>

      <section className="glass-card">
        <div className="row-between">
          <div>
            <h4 style={{ margin: 0 }}>Session</h4>
            <small style={{ color: sessionStatus === 'active' ? 'var(--success)' : 'var(--text-secondary)' }}>
              {sessionStatus === 'active' ? 'Active' : 'Not available'}
            </small>
          </div>
          <span className={`pill pill-${sessionStatus === 'active' ? 'green' : 'gray'}`}>
            {sessionStatus === 'active' ? 'ACTIVE' : 'NONE'}
          </span>
        </div>
      </section>

      {/* API / System status */}
      <SectionHeader title="System" />
      <section className="glass-card">
        <div className="row-between">
          <div>
            <h4 style={{ margin: 0 }}>API mode</h4>
            <small style={{ color: apiModeTone[apiMode] }}>{apiModeLabel[apiMode]}</small>
          </div>
          <span
            className="pill"
            style={{ backgroundColor: apiModeTone[apiMode], color: '#fff' }}
          >
            {apiMode.toUpperCase()}
          </span>
        </div>
      </section>

      {systemStatus && (
        <section className="glass-card grid-3">
          <div>
            <h4 style={{ margin: 0 }}>
              <span className={`pill pill-${systemStatus.healthy ? 'green' : 'orange'}`}>
                {systemStatus.healthy ? 'OK' : 'WARN'}
              </span>
            </h4>
            <small>System</small>
          </div>
          <div>
            <h4 style={{ margin: 0 }}>{systemStatus.database === 'ok' ? '\u2713' : '\u2717'}</h4>
            <small>Database</small>
          </div>
          <div>
            <h4 style={{ margin: 0 }}>{systemStatus.redis === 'ok' ? '\u2713' : '\u2717'}</h4>
            <small>Redis</small>
          </div>
        </section>
      )}

      {!systemStatus && (
        <section className="glass-card">
          <small style={{ color: 'var(--text-secondary)' }}>System status unavailable</small>
        </section>
      )}

      {/* Guarded mode explanation */}
      {token && (
        <>
          <SectionHeader title="Production mode" />
          <section className="glass-card">
            <div className="row-between">
              <div>
                <h4 style={{ margin: 0 }}>Guarded mode</h4>
                <small style={{ color: '#92400e' }}>Create records only</small>
              </div>
              <span className="pill pill-orange">GUARDED</span>
            </div>
            <small style={{ display: 'block', marginTop: 8, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              In production, creating agents, tasks, and topic bindings creates real database records.
              Dangerous actions (deploy, migrations, environment changes) require explicit approval
              through the approvals system. Task creation does not trigger OpenCode or command execution.
            </small>
          </section>
        </>
      )}

      {/* Product Roadmap */}
      <SectionHeader title="Product roadmap" />
      <section className="glass-card">
        <div className="roadmap-item">
          <span className="roadmap-item__dot roadmap-item__dot--planned" />
          <span className="roadmap-item__text">Local Runner</span>
          <span className="roadmap-item__badge">Planned</span>
        </div>
        <div className="roadmap-item">
          <span className="roadmap-item__dot roadmap-item__dot--planned" />
          <span className="roadmap-item__text">Cloud Workspace</span>
          <span className="roadmap-item__badge">Planned</span>
        </div>
        <div className="roadmap-item">
          <span className="roadmap-item__dot roadmap-item__dot--planned" />
          <span className="roadmap-item__text">GitHub Integration</span>
          <span className="roadmap-item__badge">Planned</span>
        </div>
        <div className="roadmap-item">
          <span className="roadmap-item__dot roadmap-item__dot--gate" />
          <span className="roadmap-item__text">Agent Execution</span>
          <span className="roadmap-item__badge">Approval-gated</span>
        </div>
        <div className="roadmap-item">
          <span className="roadmap-item__dot roadmap-item__dot--future" />
          <span className="roadmap-item__text">PR Automation</span>
          <span className="roadmap-item__badge">Future</span>
        </div>
      </section>

      {/* Public URL */}
      <SectionHeader title="Public URL" />
      <section className="glass-card">
        <h4 style={{ margin: 0, marginBottom: 4 }}>Mini App</h4>
        <small style={{ wordBreak: 'break-all', color: '#3b82f6' }}>
          https://polyrouter.ru/app/
        </small>
        <p style={{ fontSize: '0.80rem', color: 'var(--text-secondary)', marginTop: 8, marginBottom: 0 }}>
          Open this URL from the Telegram &quot;Open AI Office&quot; button for best experience.
        </p>
      </section>

      {/* Navigation links */}
      <SectionHeader title="Configuration" />
      <section className="glass-card glass-card--clickable" onClick={() => navigate('/topics')}>
        <h4 style={{ margin: 0 }}>Topic Bindings</h4>
        <small style={{ color: 'var(--text-secondary)' }}>Telegram topic \u2194 role mappings</small>
      </section>
    </PageContainer>
  );
}
