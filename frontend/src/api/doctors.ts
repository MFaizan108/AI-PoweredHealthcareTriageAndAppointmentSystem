import { api } from "./client";
import type { Doctor, Paginated } from "./types";

export interface DoctorAvailability {
  id: number;
  doctor: number;
  weekday: number;
  start_time: string;
  end_time: string;
  slot_duration_minutes: number;
  is_active: boolean;
}

export interface DoctorLeave {
  id: number;
  doctor: number;
  start_date: string;
  end_date: string;
  reason: string;
}

export async function listDoctors(params?: Record<string, string>): Promise<Doctor[]> {
  const { data } = await api.get<Paginated<Doctor> | Doctor[]>("/api/doctors/", { params });
  return Array.isArray(data) ? data : data.results;
}

export async function updateDoctorProfile(id: number, payload: Partial<Doctor>): Promise<Doctor> {
  const { data } = await api.patch<Doctor>(`/api/doctors/${id}/`, payload);
  return data;
}

export async function createDoctorProfile(payload: { user_id: number; department?: number; specialization?: string }): Promise<Doctor> {
  const { data } = await api.post<Doctor>("/api/doctors/", payload);
  return data;
}

export async function listAvailability(doctorId: number): Promise<DoctorAvailability[]> {
  const { data } = await api.get<Paginated<DoctorAvailability> | DoctorAvailability[]>("/api/doctors/availability/", {
    params: { doctor: String(doctorId) },
  });
  return Array.isArray(data) ? data : data.results;
}

export async function createAvailability(payload: Omit<DoctorAvailability, "id">): Promise<DoctorAvailability> {
  const { data } = await api.post<DoctorAvailability>("/api/doctors/availability/", payload);
  return data;
}

export async function deleteAvailability(id: number): Promise<void> {
  await api.delete(`/api/doctors/availability/${id}/`);
}

export async function listLeaves(doctorId: number): Promise<DoctorLeave[]> {
  const { data } = await api.get<Paginated<DoctorLeave> | DoctorLeave[]>("/api/doctors/leaves/", {
    params: { doctor: String(doctorId) },
  });
  return Array.isArray(data) ? data : data.results;
}

export async function createLeave(payload: Omit<DoctorLeave, "id">): Promise<DoctorLeave> {
  const { data } = await api.post<DoctorLeave>("/api/doctors/leaves/", payload);
  return data;
}

export async function deleteLeave(id: number): Promise<void> {
  await api.delete(`/api/doctors/leaves/${id}/`);
}
