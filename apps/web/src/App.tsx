import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/AppShell';
import { AgentDetailPage } from './pages/AgentDetailPage';
import { AgentsPage } from './pages/AgentsPage';
import { CreateAgentPage } from './pages/CreateAgentPage';
import { CreateTaskPage } from './pages/CreateTaskPage';
import { HomePage } from './pages/HomePage';
import { MorePage } from './pages/MorePage';
import { TasksPage } from './pages/TasksPage';
import { TopicsPage } from './pages/TopicsPage';
import { WorkspacesPage } from './pages/WorkspacesPage';

export function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/workspaces" element={<WorkspacesPage />} />
        <Route path="/agents" element={<AgentsPage />} />
        <Route path="/agents/new" element={<CreateAgentPage />} />
        <Route path="/agents/:id" element={<AgentDetailPage />} />
        <Route path="/tasks" element={<TasksPage />} />
        <Route path="/tasks/new" element={<CreateTaskPage />} />
        <Route path="/topics" element={<TopicsPage />} />
        <Route path="/more" element={<MorePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
