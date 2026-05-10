import type { PropsWithChildren } from 'react';
import { BottomNav } from './BottomNav';

export function AppShell({ children }: PropsWithChildren) {
  return (
    <div className="app-shell">
      <div className="app-content">{children}</div>
      <BottomNav />
    </div>
  );
}
