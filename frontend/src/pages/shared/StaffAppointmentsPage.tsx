import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { bookAppointment, cancelAppointment, checkInAppointment, getAvailableSlots, listAppointments } from "../../api/appointments";
import { extractErrorMessage } from "../../api/client";
import { listDoctors } from "../../api/doctors";
import type { Appointment, Patient } from "../../api/types";
import { PatientPicker } from "../../components/PatientPicker";
import { StatusBadge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatDate, formatTime } from "../../format";

function BookForPatientForm({ onBooked }: { onBooked: () => void }) {
  const queryClient = useQueryClient();
  const doctors = useQuery({ queryKey: ["doctors"], queryFn: () => listDoctors() });

  const [patient, setPatient] = useState<Patient | null>(null);
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
    mutationFn: () => {
      if (!patient) throw new Error("Select a patient first.");
      return bookAppointment({
        patient: patient.id,
        doctor: Number(doctorId),
        appointment_date: date,
        slot_start_time: slotStart,
        reason,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      onBooked();
    },
    onError: (err) => setError(extractErrorMessage(err)),
  });

  const minDate = new Date().toISOString().slice(0, 10);

  return (
    <Card title="Book an appointment for a patient">
      {error && <ErrorBanner message={error} />}
      <label className="field">
        <span>Patient</span>
        <PatientPicker value={patient} onChange={setPatient} />
      </label>
      <div className="field-row">
        <label className="field">
          <span>Doctor</span>
          <select value={doctorId} onChange={(e) => { setDoctorId(e.target.value); setSlotStart(""); }}>
            <option value="">Select a doctor</option>
            {doctors.data?.map((d) => (
              <option key={d.id} value={d.id}>
                Dr. {d.user.first_name} {d.user.last_name}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Date</span>
          <input type="date" min={minDate} value={date} onChange={(e) => { setDate(e.target.value); setSlotStart(""); }} />
        </label>
      </div>

      {doctorId && date && (
        <div className="field">
          <span>Available slots</span>
          {slots.isLoading && <Spinner />}
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
        <span>Reason (optional)</span>
        <textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={2} />
      </label>

      <button className="btn btn-primary" disabled={!patient || !slotStart || bookMutation.isPending} onClick={() => bookMutation.mutate()}>
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
  const checkInMutation = useMutation({
    mutationFn: () => checkInAppointment(appointment.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["appointments"] }),
    onError: (err) => setError(extractErrorMessage(err)),
  });

  const canCancel = !["cancelled", "completed", "no_show"].includes(appointment.status);

  return (
    <div className="list-row list-row-bordered">
      <div>
        <div className="list-row-title">
          {appointment.patient_detail.user.first_name} {appointment.patient_detail.user.last_name} with Dr.{" "}
          {appointment.doctor_detail.user.first_name} {appointment.doctor_detail.user.last_name}
        </div>
        <div className="list-row-subtitle">
          {formatDate(appointment.appointment_date)} at {formatTime(appointment.slot_start_time)} &middot; Token{" "}
          {appointment.token_number}
        </div>
        {error && <ErrorBanner message={error} />}
      </div>
      <div className="list-row-actions">
        <StatusBadge status={appointment.status} />
        {/* AppointmentSerializer doesn't expose `checked_in` — "pending" is the only status
            check-in actually transitions out of (it sets status to "confirmed"), so it's the
            reliable proxy for "not yet checked in" available from the API response. */}
        {appointment.status === "pending" && (
          <button className="btn btn-ghost" disabled={checkInMutation.isPending} onClick={() => checkInMutation.mutate()}>
            Check in
          </button>
        )}
        {canCancel && (
          <button className="btn btn-ghost btn-danger" disabled={cancelMutation.isPending} onClick={() => cancelMutation.mutate()}>
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}

export function StaffAppointmentsPage() {
  const [showForm, setShowForm] = useState(false);
  const [dateFilter, setDateFilter] = useState("");
  const appointments = useQuery({
    queryKey: ["appointments", dateFilter],
    queryFn: () => listAppointments(dateFilter ? { date: dateFilter } : undefined),
  });

  const sorted = [...(appointments.data ?? [])].sort((a, b) =>
    `${b.appointment_date}${b.slot_start_time}`.localeCompare(`${a.appointment_date}${a.slot_start_time}`),
  );

  return (
    <div className="page-stack">
      <div className="page-heading-row">
        <h2 className="page-heading">Appointments</h2>
        <div className="quick-actions">
          <input type="date" value={dateFilter} onChange={(e) => setDateFilter(e.target.value)} />
          <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
            {showForm ? "Close" : "Book new appointment"}
          </button>
        </div>
      </div>

      {showForm && <BookForPatientForm onBooked={() => setShowForm(false)} />}

      <Card title="All appointments">
        {appointments.isLoading && <Spinner />}
        {appointments.isError && <ErrorBanner message="Could not load appointments." />}
        {!appointments.isLoading && sorted.length === 0 && <EmptyState message="No appointments found." />}
        {sorted.map((a) => (
          <AppointmentRow key={a.id} appointment={a} />
        ))}
      </Card>
    </div>
  );
}
