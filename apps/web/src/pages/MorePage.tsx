import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';
import { getTelegramContext } from '../lib/telegram';
import { getSessionToken } from '../api/client';

export function MorePage() {
  const navigate = useNavigate();
  const context = useMemo(() => getTelegramContext(), []);
  const token = getSessionToken();

  return (
    <PageContainer>
      <Header title="More" subtitle="Environment and utility" />
      <section className="card" style={{ cursor: 'pointer' }} onClick={() => navigate('/topics')}>
        <h3>Topic Bindings</h3>
        <p style={{ fontSize: '0.85rem', color: '#6b7280' }}>View and register Telegram topic ↔ role mappings</p>
      </section>
      <section className="card">
        <h3>Telegram WebApp</h3>
        <p>{context.isTelegramWebApp ? 'Connected' : 'Browser preview mode'}</p>
      </section>
      <section className="card">
        <h3>Auth session</h3>
        <p style={{ fontSize: '0.82rem', color: token ? '#166534' : '#6b7280' }}>
          {token ? `Active (${token.slice(0, 8)}…)` : 'Not authenticated'}
        </p>
      </section>
      <section className="card">
        <h3>Init data</h3>
        <small style={{ wordBreak: 'break-all' }}>
          {context.initData ? `${context.initData.slice(0, 60)}…` : 'No initData available'}
        </small>
      </section>
      <section className="card">
        <h3>Unsafe payload keys</h3>
        <small>{Object.keys(context.initDataUnsafe).join(', ') || 'No payload keys'}</small>
      </section>
    </PageContainer>
  );
}
