import { api } from "./client";
import type { Appointment, AppointmentStatus, AvailableSlot, Feedback, Paginated, QueueEntry, Waitlist } from "./types";

export async function listAppointments(params?: Record<string, string>): Promise<Appointment[]> {
  const { data } = await api.get<Paginated<Appointment> | Appointment[]>("/api/appointments/", { params });
  return Array.isArray(data) ? data : data.results;
}

export async function getQueue(params?: { doctor?: number; date?: string }): Promise<QueueEntry[]> {
  const { data } = await api.get<QueueEntry[]>("/api/appointments/queue/", {
    params: { ...(params?.doctor ? { doctor: params.doctor } : {}), ...(params?.date ? { date: params.date } : {}) },
  });
  return data;
}

export async function checkInAppointment(id: number): Promise<Appointment> {
  const { data } = await api.post<Appointment>(`/api/appointments/${id}/check-in/`);
  return data;
}

export async function setAppointmentStatus(id: number, status: AppointmentStatus): Promise<Appointment> {
  const { data } = await api.post<Appointment>(`/api/appointments/${id}/set-status/`, { status });
  return data;
}

export async function getAvailableSlots(doctorId: number, date: string): Promise<AvailableSlot[]> {
  const { data } = await api.get<AvailableSlot[]>("/api/appointments/available-slots/", {
    params: { doctor: doctorId, date },
  });
  // The backend generates slots per DoctorAvailability row and doesn't dedupe across rows
  // (appointments/services.py get_available_slots) — a doctor with two overlapping/duplicate
  // windows for the same weekday legitimately gets duplicate start_times back. Deduped here,
  // once, for every caller rather than in each page that renders a slot picker.
  const seen = new Set<string>();
  return data.filter((slot) => {
    if (seen.has(slot.start_time)) return false;
    seen.add(slot.start_time);
    return true;
  });
}

export interface BookAppointmentPayload {
  doctor: number;
  appointment_date: string;
  slot_start_time: string;
  reason?: string;
  /** Required when booking is done by staff (receptionist/admin) on a patient's behalf — a
   * patient user never sends this, the backend injects their own patient record instead. */
  patient?: number;
}

export async function bookAppointment(payload: BookAppointmentPayload): Promise<Appointment> {
  const { data } = await api.post<Appointment>("/api/appointments/", payload);
  return data;
}

export async function cancelAppointment(id: number): Promise<Appointment> {
  const { data } = await api.post<Appointment>(`/api/appointments/${id}/cancel/`);
  return data;
}

export async function listFeedback(params?: Record<string, string>): Promise<Feedback[]> {
  const { data } = await api.get<Paginated<Feedback> | Feedback[]>("/api/appointments/feedback/", { params });
  return Array.isArray(data) ? data : data.results;
}

export async function leaveFeedback(payload: { appointment: number; rating: number; comment?: string }): Promise<Feedback> {
  const { data } = await api.post<Feedback>("/api/appointments/feedback/", payload);
  return data;
}

export async function listWaitlist(params?: Record<string, string>): Promise<Waitlist[]> {
  const { data } = await api.get<Paginated<Waitlist> | Waitlist[]>("/api/appointments/waitlist/", { params });
  return Array.isArray(data) ? data : data.results;
}

export async function joinWaitlist(payload: { doctor: number; preferred_date: string; notes?: string }): Promise<Waitlist> {
  const { data } = await api.post<Waitlist>("/api/appointments/waitlist/", payload);
  return data;
}

export async function leaveWaitlist(id: number): Promise<Waitlist> {
  const { data } = await api.post<Waitlist>(`/api/appointments/waitlist/${id}/leave/`);
  return data;
}
