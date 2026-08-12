import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getAppointmentAnalytics, getPatientAnalytics } from "../../api/analytics";
import { Card } from "../../components/ui/Card";
import { Spinner } from "../../components/ui/Spinner";

export function AdminOverviewPage() {
  const patientStats = useQuery({ queryKey: ["analytics", "patients"], queryFn: getPatientAnalytics });
  const appointmentStats = useQuery({ queryKey: ["analytics", "appointments"], queryFn: getAppointmentAnalytics });

  const isLoading = patientStats.isLoading || appointmentStats.isLoading;

  return (
    <div className="page-stack">
      <h2 className="page-heading">Admin Overview</h2>

      {isLoading ? (
        <Spinner />
      ) : (
        <div className="stat-grid">
          <Card title="Total patients">
            <div className="stat-number">{patientStats.data?.total_patients ?? 0}</div>
          </Card>
          <Card title="New this month">
            <div className="stat-number">{patientStats.data?.new_patients_this_month ?? 0}</div>
          </Card>
          <Card title="Total appointments">
            <div className="stat-number">{appointmentStats.data?.total_appointments ?? 0}</div>
          </Card>
          <Card title="Avg. wait time">
            <div className="stat-number">
              {appointmentStats.data?.average_waiting_time_minutes != null
                ? `${appointmentStats.data.average_waiting_time_minutes}m`
                : "-"}
            </div>
          </Card>
        </div>
      )}

      <Card title="Quick links">
        <div className="quick-actions">
          <Link to="/admin/users" className="btn btn-secondary">Manage Users</Link>
          <Link to="/admin/doctors" className="btn btn-secondary">Manage Doctors</Link>
          <Link to="/admin/departments" className="btn btn-secondary">Departments</Link>
          <Link to="/admin/analytics" className="btn btn-secondary">Full Analytics</Link>
        </div>
      </Card>
    </div>
  );
}
