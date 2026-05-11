import { NavLink } from 'react-router-dom';
import { FolderIcon, HomeIcon, MoreIcon, RobotIcon, TaskIcon } from './ui/icons';

const links = [
  { to: '/', label: 'Home', icon: HomeIcon },
  { to: '/workspaces', label: 'Spaces', icon: FolderIcon },
  { to: '/agents', label: 'Agents', icon: RobotIcon },
  { to: '/tasks', label: 'Tasks', icon: TaskIcon },
  { to: '/more', label: 'More', icon: MoreIcon },
];

export function BottomNav() {
  return (
    <nav className="bottom-nav" aria-label="Primary navigation">
      {links.map((link) => (
        <NavLink key={link.to} to={link.to} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="nav-item__icon"><link.icon width={16} height={16} /></span>
          <span className="nav-item__label">{link.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
