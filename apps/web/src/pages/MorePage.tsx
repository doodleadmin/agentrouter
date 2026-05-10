import { useMemo } from 'react';
import { Header } from '../components/Header';
import { PageContainer } from '../components/PageContainer';
import { getTelegramContext } from '../lib/telegram';

export function MorePage() {
  const context = useMemo(() => getTelegramContext(), []);

  return (
    <PageContainer>
      <Header title="More" subtitle="Environment and utility" />
      <section className="card">
        <h3>Telegram WebApp</h3>
        <p>{context.isTelegramWebApp ? 'Connected' : 'Browser preview mode'}</p>
      </section>
      <section className="card">
        <h3>Init data</h3>
        <small>{context.initData ?? 'No initData available'}</small>
      </section>
      <section className="card">
        <h3>Unsafe payload keys</h3>
        <small>{Object.keys(context.initDataUnsafe).join(', ') || 'No payload keys'}</small>
      </section>
    </PageContainer>
  );
}
