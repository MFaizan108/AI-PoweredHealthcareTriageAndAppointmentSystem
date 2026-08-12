import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { listAppointments, setAppointmentStatus } from "../../api/appointments";
import { extractErrorMessage } from "../../api/client";
import type { Appointment, AppointmentStatus } from "../../api/types";
import { StatusBadge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatDate, formatTime } from "../../format";

const NEXT_STATUS: Partial<Record<AppointmentStatus, { label: string; status: AppointmentStatus }[]>> = {
  confirmed: [{ label: "Start consultation", status: "in_consultation" }, { label: "Mark no-show", status: "no_show" }],
  pending: [{ label: "Start consultation", status: "in_consultation" }, { label: "Mark no-show", status: "no_show" }],
  in_consultation: [{ label: "Complete", status: "completed" }],
};

function AppointmentRow({ appointment }: { appointment: Appointment }) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const statusMutation = useMutation({
    mutationFn: (status: AppointmentStatus) => setAppointmentStatus(appointment.id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["appointments"] }),
    onError: (err) => setError(extractErrorMessage(err)),
  });

  const actions = NEXT_STATUS[appointment.status] ?? [];

  return (
    <div className="list-row list-row-bordered">
      <div>
        <div className="list-row-title">
          {appointment.patient_detail.user.first_name} {appointment.patient_detail.user.last_name}
        </div>
        <div className="list-row-subtitle">
          {formatDate(appointment.appointment_date)} at {formatTime(appointment.slot_start_time)} &middot; Token{" "}
          {appointment.token_number}
        </div>
        {appointment.reason && <div className="list-row-meta">{appointment.reason}</div>}
        {error && <ErrorBanner message={error} />}
      </div>
      <div className="list-row-actions">
        <StatusBadge status={appointment.status} />
        {actions.map((a) => (
          <button
            key={a.status}
            className="btn btn-ghost"
            disabled={statusMutation.isPending}
            onClick={() => statusMutation.mutate(a.status)}
          >
            {a.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export function DoctorAppointmentsPage() {
  const appointments = useQuery({ queryKey: ["appointments"], queryFn: () => listAppointments() });

  const sorted = [...(appointments.data ?? [])].sort((a, b) =>
    `${b.appointment_date}${b.slot_start_time}`.localeCompare(`${a.appointment_date}${a.slot_start_time}`),
  );

  return (
    <div className="page-stack">
      <h2 className="page-heading">Appointments</h2>
      <Card>
        {appointments.isLoading && <Spinner />}
        {appointments.isError && <ErrorBanner message="Could not load appointments." />}
        {!appointments.isLoading && sorted.length === 0 && <EmptyState message="No appointments yet." />}
        {sorted.map((a) => (
          <AppointmentRow key={a.id} appointment={a} />
        ))}
      </Card>
    </div>
  );
}
