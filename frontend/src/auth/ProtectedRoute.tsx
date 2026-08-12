import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./AuthContext";
import { Spinner } from "../components/ui/Spinner";

export function ProtectedRoute() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="full-page-center">
        <Spinner />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
