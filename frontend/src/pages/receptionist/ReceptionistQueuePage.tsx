import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { checkInAppointment, getQueue, listAppointments } from "../../api/appointments";
import { extractErrorMessage } from "../../api/client";
import { listDoctors } from "../../api/doctors";
import { Badge, StatusBadge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatTime } from "../../format";

export function ReceptionistQueuePage() {
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [doctorId, setDoctorId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const doctors = useQuery({ queryKey: ["doctors"], queryFn: () => listDoctors() });
  const queue = useQuery({
    queryKey: ["queue", date, doctorId],
    queryFn: () => getQueue({ date, doctor: doctorId ? Number(doctorId) : undefined }),
  });
  // Needed to resolve a queue entry's appointment id for the check-in action (the queue endpoint
  // returns a lightweight projection without one — see appointments/views.py's `queue` action).
  const appointments = useQuery({ queryKey: ["appointments", "for-checkin", date], queryFn: () => listAppointments({ date }) });

  const checkInMutation = useMutation({
    mutationFn: checkInAppointment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["queue"] });
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
    },
    onError: (err) => setError(extractErrorMessage(err)),
  });

  return (
    <div className="page-stack">
      <div className="page-heading-row">
        <h2 className="page-heading">Queue</h2>
        <div className="quick-actions">
          <select value={doctorId} onChange={(e) => setDoctorId(e.target.value)}>
            <option value="">All doctors</option>
            {doctors.data?.map((d) => (
              <option key={d.id} value={d.id}>
                Dr. {d.user.first_name} {d.user.last_name}
              </option>
            ))}
          </select>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      <Card>
        {queue.isLoading && <Spinner />}
        {queue.isError && <ErrorBanner message="Could not load the queue." />}
        {!queue.isLoading && (queue.data ?? []).length === 0 && <EmptyState message="No appointments for this date." />}
        {queue.data?.map((entry, i) => {
          const appointment = appointments.data?.find((a) => a.token_number === entry.token_number);
          return (
            <div key={`${entry.token_number}-${i}`} className="list-row list-row-bordered">
              <div>
                <div className="list-row-title">
                  Token {entry.token_number} &middot; {entry.patient}
                </div>
                <div className="list-row-subtitle">
                  {entry.doctor} &middot; {formatTime(entry.slot_start_time)}
                </div>
              </div>
              <div className="list-row-actions">
                {entry.checked_in ? (
                  <Badge tone="info">Checked in</Badge>
                ) : (
                  appointment && (
                    <button
                      className="btn btn-secondary"
                      disabled={checkInMutation.isPending}
                      onClick={() => checkInMutation.mutate(appointment.id)}
                    >
                      Check in
                    </button>
                  )
                )}
                <StatusBadge status={entry.status} />
              </div>
            </div>
          );
        })}
      </Card>
    </div>
  );
}
