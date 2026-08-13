import { NavLink } from "react-router-dom";

export interface NavItem {
  to: string;
  label: string;
  icon: string;
}

export function Sidebar({
  items,
  roleLabel,
  mobileOpen = false,
  onNavigate,
}: {
  items: NavItem[];
  roleLabel: string;
  mobileOpen?: boolean;
  onNavigate?: () => void;
}) {
  return (
    <aside className={`sidebar${mobileOpen ? " sidebar-mobile-open" : ""}`}>
      <div className="sidebar-brand">
        <span className="sidebar-brand-mark">+</span>
        <div>
          <div className="sidebar-brand-name">Healthcare Triage</div>
          <div className="sidebar-brand-role">{roleLabel}</div>
        </div>
      </div>
      <nav className="sidebar-nav">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={({ isActive }) => `sidebar-link${isActive ? " sidebar-link-active" : ""}`}
          >
            <span className="sidebar-link-icon" aria-hidden="true">
              {item.icon}
            </span>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
