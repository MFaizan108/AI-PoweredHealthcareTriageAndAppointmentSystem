import { Outlet } from "react-router-dom";
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
  return (
    <div className="app-shell">
      <Sidebar items={items} roleLabel={roleLabel} />
      <div className="app-main">
        <Topbar title={title} notificationsPath={notificationsPath} />
        <main className="app-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
