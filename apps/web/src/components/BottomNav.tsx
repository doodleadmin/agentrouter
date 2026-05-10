import { NavLink } from 'react-router-dom';

const links = [
  { to: '/', label: 'Home' },
  { to: '/agents', label: 'Agents' },
  { to: '/tasks', label: 'Tasks' },
  { to: '/more', label: 'More' },
];

export function BottomNav() {
  return (
    <nav className="bottom-nav">
      {links.map((link) => (
        <NavLink key={link.to} to={link.to} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          {link.label}
        </NavLink>
      ))}
    </nav>
  );
}
