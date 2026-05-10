import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import type { SystemStatusSummary } from '../types';
import { getTelegramContext } from '../lib/telegram';
import { getSessionToken } from '../api/client';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';

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
    // Attempted auth via Telegram WebApp, token exists = verified
    return 'verified';
  }, [context.isTelegramWebApp, token]);

  const sessionStatus: SessionStatus = token ? 'active' : 'unavailable';

  const authStatusLabel: Record<AuthStatus, string> = {
    preview: 'Preview mode: opened outside Telegram',
    pending: 'Auth pending…',
    verified: 'Telegram session verified',
    failed: 'Auth failed, retry',
    unavailable: 'Auth unavailable',
  };

  const authStatusTone: Record<AuthStatus, string> = {
    preview: '#6b7280',
    pending: '#f59e0b',
    verified: '#166534',
    failed: '#dc2626',
    unavailable: '#6b7280',
  };

  const apiModeLabel: Record<ApiMode, string> = {
    live: 'Live API',
    mock: 'Preview data',
    preview: 'Preview mode',
    error: 'API unavailable',
  };

  const apiModeTone: Record<ApiMode, string> = {
    live: '#166534',
    mock: '#6b7280',
    preview: '#6b7280',
    error: '#dc2626',
  };

  return (
    <PageContainer>
      <Header title="Settings" subtitle="Environment &amp; diagnostics" />

      {/* Auth & Session — safe only, no raw values */}
      <div className="section-title">Authentication</div>
      <section className="card">
        <div className="row-between">
          <div>
            <h4 style={{ margin: 0 }}>Telegram WebApp</h4>
            <small style={{ color: '#6b7280' }}>
              {context.isTelegramWebApp ? 'Detected' : 'Not detected (browser preview)'}
            </small>
          </div>
          <span className={`pill pill-${context.isTelegramWebApp ? 'green' : 'gray'}`}>
            {context.isTelegramWebApp ? 'ON' : 'OFF'}
          </span>
        </div>
      </section>

      <section className="card">
        <div className="row-between">
          <div>
            <h4 style={{ margin: 0 }}>Auth status</h4>
            <small style={{ color: authStatusTone[authStatus] }}>{authStatusLabel[authStatus]}</small>
          </div>
          <span
            className={`pill`}
            style={{ backgroundColor: authStatusTone[authStatus], color: '#fff' }}
          >
            {authStatus.toUpperCase()}
          </span>
        </div>
      </section>

      <section className="card">
        <div className="row-between">
          <div>
            <h4 style={{ margin: 0 }}>Session</h4>
            <small style={{ color: sessionStatus === 'active' ? '#166534' : '#6b7280' }}>
              {sessionStatus === 'active' ? 'Active' : 'Not available'}
            </small>
          </div>
          <span className={`pill pill-${sessionStatus === 'active' ? 'green' : 'gray'}`}>
            {sessionStatus === 'active' ? 'ACTIVE' : 'NONE'}
          </span>
        </div>
      </section>

      {/* API / System status */}
      <div className="section-title">System</div>
      <section className="card">
        <div className="row-between">
          <div>
            <h4 style={{ margin: 0 }}>API mode</h4>
            <small style={{ color: apiModeTone[apiMode] }}>{apiModeLabel[apiMode]}</small>
          </div>
          <span
            className={`pill`}
            style={{ backgroundColor: apiModeTone[apiMode], color: '#fff' }}
          >
            {apiMode.toUpperCase()}
          </span>
        </div>
      </section>

      {systemStatus && (
        <section className="card grid-3">
          <div>
            <h4 style={{ margin: 0 }}>
              <span className={`pill pill-${systemStatus.healthy ? 'green' : 'orange'}`}>
                {systemStatus.healthy ? 'OK' : 'WARN'}
              </span>
            </h4>
            <small>System</small>
          </div>
          <div>
            <h4 style={{ margin: 0 }}>{systemStatus.database === 'ok' ? '✓' : '✗'}</h4>
            <small>Database</small>
          </div>
          <div>
            <h4 style={{ margin: 0 }}>{systemStatus.redis === 'ok' ? '✓' : '✗'}</h4>
            <small>Redis</small>
          </div>
        </section>
      )}

      {!systemStatus && (
        <section className="card">
          <small style={{ color: '#6b7280' }}>System status unavailable</small>
        </section>
      )}

      {/* Guarded mode explanation */}
      {token && (
        <>
          <div className="section-title">Production mode</div>
          <section className="card">
            <div className="row-between">
              <div>
                <h4 style={{ margin: 0 }}>Guarded mode</h4>
                <small style={{ color: '#92400e' }}>Create records only</small>
              </div>
              <span className="pill pill-orange">GUARDED</span>
            </div>
            <small style={{ display: 'block', marginTop: 8, color: '#6b7280', lineHeight: 1.5 }}>
              In production, creating agents, tasks, and topic bindings creates real database records.
              Dangerous actions (deploy, migrations, environment changes) require explicit approval
              through the approvals system. Task creation does not trigger OpenCode or command execution.
            </small>
          </section>
        </>
      )}

      {/* Production links */}
      <div className="section-title">Public URL</div>
      <section className="card">
        <h4 style={{ margin: 0, marginBottom: 4 }}>Mini App</h4>
        <small style={{ wordBreak: 'break-all', color: '#3b82f6' }}>
          https://polyrouter.ru/app/
        </small>
        <p style={{ fontSize: '0.80rem', color: '#6b7280', marginTop: 8, marginBottom: 0 }}>
          Open this URL from the Telegram &quot;Open AI Office&quot; button for best experience.
        </p>
      </section>

      {/* Navigation links */}
      <div className="section-title">Configuration</div>
      <section className="card" style={{ cursor: 'pointer' }} onClick={() => navigate('/topics')}>
        <h4 style={{ margin: 0 }}>Topic Bindings</h4>
        <small style={{ color: '#6b7280' }}>Telegram topic ↔ role mappings</small>
      </section>
    </PageContainer>
  );
}
