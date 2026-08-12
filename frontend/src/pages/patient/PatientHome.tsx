import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listAppointments } from "../../api/appointments";
import { listInvoices } from "../../api/billing";
import { listNotifications } from "../../api/notifications";
import { useAuth } from "../../auth/AuthContext";
import { Card } from "../../components/ui/Card";
import { StatusBadge } from "../../components/ui/Badge";
import { Spinner } from "../../components/ui/Spinner";
import { formatDate, formatTime } from "../../format";

export function PatientHome() {
  const { user } = useAuth();

  const appointments = useQuery({ queryKey: ["appointments"], queryFn: () => listAppointments() });
  const invoices = useQuery({ queryKey: ["invoices"], queryFn: () => listInvoices() });
  const notifications = useQuery({ queryKey: ["notifications", "unread"], queryFn: () => listNotifications(true) });

  const today = new Date().toISOString().slice(0, 10);
  const upcoming = (appointments.data ?? [])
    .filter((a) => a.appointment_date >= today && !["cancelled", "completed", "no_show"].includes(a.status))
    .sort((a, b) => a.appointment_date.localeCompare(b.appointment_date));

  const unpaidTotal = (invoices.data ?? [])
    .filter((i) => i.status !== "paid" && i.status !== "cancelled")
    .reduce((sum, i) => sum + Number(i.balance_due), 0);

  return (
    <div className="page-stack">
      <h2 className="page-heading">Welcome back, {user?.first_name || user?.username}</h2>

      <div className="stat-grid">
        <Card title="Upcoming appointments">
          {appointments.isLoading ? <Spinner /> : <div className="stat-number">{upcoming.length}</div>}
        </Card>
        <Card title="Unread notifications">
          {notifications.isLoading ? <Spinner /> : <div className="stat-number">{notifications.data?.length ?? 0}</div>}
        </Card>
        <Card title="Outstanding balance">
          {invoices.isLoading ? <Spinner /> : <div className="stat-number">Rs {unpaidTotal.toFixed(2)}</div>}
        </Card>
      </div>

      <Card
        title="Next appointments"
        actions={
          <Link to="/patient/appointments" className="link-button">
            View all
          </Link>
        }
      >
        {appointments.isLoading && <Spinner />}
        {!appointments.isLoading && upcoming.length === 0 && <p className="empty-state">No upcoming appointments.</p>}
        {upcoming.slice(0, 5).map((a) => (
          <div key={a.id} className="list-row">
            <div>
              <div className="list-row-title">Dr. {a.doctor_detail.user.first_name} {a.doctor_detail.user.last_name}</div>
              <div className="list-row-subtitle">
                {formatDate(a.appointment_date)} at {formatTime(a.slot_start_time)} &middot; Token {a.token_number}
              </div>
            </div>
            <StatusBadge status={a.status} />
          </div>
        ))}
      </Card>

      <Card title="Quick actions">
        <div className="quick-actions">
          <Link to="/patient/triage" className="btn btn-primary">
            Start AI Triage
          </Link>
          <Link to="/patient/appointments?book=1" className="btn btn-secondary">
            Book Appointment
          </Link>
        </div>
      </Card>
    </div>
  );
}
