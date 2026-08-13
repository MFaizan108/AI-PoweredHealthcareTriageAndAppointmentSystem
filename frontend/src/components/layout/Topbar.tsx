import { useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { NotificationBell } from "./NotificationBell";

export function Topbar({
  title,
  notificationsPath,
  onMenuClick,
}: {
  title: string;
  notificationsPath: string;
  onMenuClick?: () => void;
}) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  const fullName = user ? [user.first_name, user.last_name].filter(Boolean).join(" ") || user.username : "";

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button type="button" className="topbar-menu-btn" onClick={onMenuClick} aria-label="Toggle navigation menu">
          &#9776;
        </button>
        <h1 className="topbar-title">{title}</h1>
      </div>
      <div className="topbar-actions">
        <NotificationBell notificationsPath={notificationsPath} />
        <span className="topbar-user">{fullName}</span>
        <button className="btn btn-ghost" onClick={handleLogout}>
          Log out
        </button>
      </div>
    </header>
  );
}
