import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/AppShell';
import { AgentDetailPage } from './pages/AgentDetailPage';
import { AgentsPage } from './pages/AgentsPage';
import { HomePage } from './pages/HomePage';
import { MorePage } from './pages/MorePage';
import { TasksPage } from './pages/TasksPage';

export function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/agents" element={<AgentsPage />} />
        <Route path="/agents/:id" element={<AgentDetailPage />} />
        <Route path="/tasks" element={<TasksPage />} />
        <Route path="/more" element={<MorePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
