import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Sidebar, type NavItem } from "./Sidebar";
import { Topbar } from "./Topbar";

export function DashboardLayout({
  items,
  roleLabel,
  title,
  notificationsPath,
}: {
  items: NavItem[];
  roleLabel: string;
  title: string;
  notificationsPath: string;
}) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const location = useLocation();

  // Close the mobile drawer automatically on navigation (e.g. back/forward, programmatic nav).
  useEffect(() => {
    setMobileNavOpen(false);
  }, [location.pathname]);

  return (
    <div className="app-shell">
      {mobileNavOpen && <div className="sidebar-backdrop" onClick={() => setMobileNavOpen(false)} />}
      <Sidebar items={items} roleLabel={roleLabel} mobileOpen={mobileNavOpen} onNavigate={() => setMobileNavOpen(false)} />
      <div className="app-main">
        <Topbar title={title} notificationsPath={notificationsPath} onMenuClick={() => setMobileNavOpen((v) => !v)} />
        <main className="app-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
