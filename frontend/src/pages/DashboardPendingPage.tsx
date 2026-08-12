import { useAuth } from "../auth/AuthContext";

export function DashboardPendingPage() {
  const { user, logout } = useAuth();

  return (
    <div className="full-page-center">
      <div className="auth-card" style={{ textAlign: "center" }}>
        <h1 className="auth-title">Welcome, {user?.first_name || user?.username}</h1>
        <p className="auth-subtitle">
          The {user?.role} dashboard hasn't been built yet — this phase shipped the Patient
          dashboard first. It's coming in a follow-up pass.
        </p>
        <button className="btn btn-primary" onClick={() => logout()}>
          Log out
        </button>
      </div>
    </div>
  );
}
