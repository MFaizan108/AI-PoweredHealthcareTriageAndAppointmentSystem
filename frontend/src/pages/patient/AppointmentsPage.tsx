import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { bookAppointment, cancelAppointment, getAvailableSlots, listAppointments } from "../../api/appointments";
import { extractErrorMessage } from "../../api/client";
import { listDoctors } from "../../api/doctors";
import type { Appointment } from "../../api/types";
import { StatusBadge, statusTone } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatDate, formatTime } from "../../format";

function BookAppointmentForm({ onBooked }: { onBooked: () => void }) {
  const queryClient = useQueryClient();
  const doctors = useQuery({ queryKey: ["doctors"], queryFn: () => listDoctors() });

  const [doctorId, setDoctorId] = useState("");
  const [date, setDate] = useState("");
  const [slotStart, setSlotStart] = useState("");
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  const slots = useQuery({
    queryKey: ["available-slots", doctorId, date],
    queryFn: () => getAvailableSlots(Number(doctorId), date),
    enabled: Boolean(doctorId && date),
  });

  const bookMutation = useMutation({
    mutationFn: () =>
      bookAppointment({ doctor: Number(doctorId), appointment_date: date, slot_start_time: slotStart, reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      onBooked();
    },
    onError: (err) => setError(extractErrorMessage(err)),
  });

  const minDate = new Date().toISOString().slice(0, 10);

  return (
    <Card title="Book an appointment">
      {error && <ErrorBanner message={error} />}
      <div className="field-row">
        <label className="field">
          <span>Doctor</span>
          <select value={doctorId} onChange={(e) => { setDoctorId(e.target.value); setSlotStart(""); }}>
            <option value="">Select a doctor</option>
            {doctors.data?.map((d) => (
              <option key={d.id} value={d.id}>
                Dr. {d.user.first_name} {d.user.last_name} &mdash; {d.specialization || d.department_name}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Date</span>
          <input
            type="date"
            min={minDate}
            value={date}
            onChange={(e) => { setDate(e.target.value); setSlotStart(""); }}
          />
        </label>
      </div>

      {doctorId && date && (
        <div className="field">
          <span>Available slots</span>
          {slots.isLoading && <Spinner />}
          {slots.data && slots.data.length === 0 && <EmptyState icon="🗓️" message="No slots configured for this date." />}
          <div className="slot-grid">
            {slots.data?.map((s) => (
              <button
                type="button"
                key={s.start_time}
                disabled={!s.available}
                className={`slot-chip${slotStart === s.start_time ? " slot-chip-selected" : ""}`}
                onClick={() => setSlotStart(s.start_time)}
              >
                {formatTime(s.start_time)}
              </button>
            ))}
          </div>
        </div>
      )}

      <label className="field">
        <span>Reason for visit (optional)</span>
        <textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={2} />
      </label>

      <button
        type="button"
        className="btn btn-primary"
        disabled={!slotStart || bookMutation.isPending}
        onClick={() => bookMutation.mutate()}
      >
        {bookMutation.isPending ? "Booking..." : "Confirm booking"}
      </button>
    </Card>
  );
}

function AppointmentRow({ appointment }: { appointment: Appointment }) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const cancelMutation = useMutation({
    mutationFn: () => cancelAppointment(appointment.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["appointments"] }),
    onError: (err) => setError(extractErrorMessage(err)),
  });

  const canCancel = !["cancelled", "completed", "no_show"].includes(appointment.status);

  return (
    <div className={`list-row list-row-bordered list-row-accent list-row-accent-${statusTone(appointment.status)}`}>
      <div>
        <div className="list-row-title">
          Dr. {appointment.doctor_detail.user.first_name} {appointment.doctor_detail.user.last_name}
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
        {canCancel && (
          <button className="btn btn-ghost btn-danger" disabled={cancelMutation.isPending} onClick={() => cancelMutation.mutate()}>
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}

export function AppointmentsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [showForm, setShowForm] = useState(searchParams.get("book") === "1");

  const appointments = useQuery({ queryKey: ["appointments"], queryFn: () => listAppointments() });

  const sorted = [...(appointments.data ?? [])].sort((a, b) =>
    `${b.appointment_date}${b.slot_start_time}`.localeCompare(`${a.appointment_date}${a.slot_start_time}`),
  );

  return (
    <div className="page-stack">
      <div className="page-heading-row">
        <h2 className="page-heading">Appointments</h2>
        <button
          className="btn btn-primary"
          onClick={() => {
            setShowForm((v) => !v);
            setSearchParams({});
          }}
        >
          {showForm ? "Close" : "Book new appointment"}
        </button>
      </div>

      {showForm && <BookAppointmentForm onBooked={() => setShowForm(false)} />}

      <Card title="Your appointments">
        {appointments.isLoading && <Spinner />}
        {appointments.isError && <ErrorBanner message="Could not load appointments." />}
        {!appointments.isLoading && sorted.length === 0 && (
          <EmptyState
            icon="📅"
            message="No appointments yet."
            action={
              <button className="btn btn-primary" onClick={() => setShowForm(true)}>
                Book your first appointment
              </button>
            }
          />
        )}
        {sorted.map((a) => (
          <AppointmentRow key={a.id} appointment={a} />
        ))}
      </Card>
    </div>
  );
}
