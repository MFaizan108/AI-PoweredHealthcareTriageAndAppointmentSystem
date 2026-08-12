import { Navigate } from "react-router-dom";
import type { Role } from "../api/types";
import { landingPathForRole } from "../roleRouting";
import { useAuth } from "./AuthContext";

/** Keeps a role's dashboard tree from being reachable by another logged-in role (e.g. a
 * receptionist following a stale bookmark into /admin) — bounces to that user's own landing page
 * instead of rendering someone else's nav shell. */
export function RoleGuard({ role, children }: { role: Role; children: React.ReactNode }) {
  const { user } = useAuth();
  if (user && user.role !== role) return <Navigate to={landingPathForRole(user.role)} replace />;
  return <>{children}</>;
}
