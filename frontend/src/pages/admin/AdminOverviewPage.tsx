import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getAppointmentAnalytics, getPatientAnalytics } from "../../api/analytics";
import { Card } from "../../components/ui/Card";
import { Spinner } from "../../components/ui/Spinner";
import { StatCard } from "../../components/ui/StatCard";

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
          <StatCard icon="🧑‍🤝‍🧑" label="Total patients" value={patientStats.data?.total_patients ?? 0} />
          <StatCard icon="✨" tone="accent" label="New this month" value={patientStats.data?.new_patients_this_month ?? 0} />
          <StatCard icon="📅" tone="success" label="Total appointments" value={appointmentStats.data?.total_appointments ?? 0} />
          <StatCard
            icon="⏱️"
            tone="warning"
            label="Avg. wait time"
            value={
              appointmentStats.data?.average_waiting_time_minutes != null
                ? `${appointmentStats.data.average_waiting_time_minutes}m`
                : "-"
            }
          />
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
