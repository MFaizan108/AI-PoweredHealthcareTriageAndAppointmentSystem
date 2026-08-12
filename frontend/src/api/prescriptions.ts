import { api } from "./client";
import type { Paginated, Prescription } from "./types";

export async function listPrescriptions(params?: Record<string, string>): Promise<Prescription[]> {
  const { data } = await api.get<Paginated<Prescription> | Prescription[]>("/api/prescriptions/", { params });
  return Array.isArray(data) ? data : data.results;
}

export async function downloadPrescriptionPdf(id: number): Promise<Blob> {
  const { data } = await api.get(`/api/prescriptions/${id}/pdf/`, { responseType: "blob" });
  return data;
}

export interface PrescriptionItemPayload {
  medicine_name: string;
  dosage: string;
  frequency: string;
  duration: string;
  instructions?: string;
}

export interface CreatePrescriptionPayload {
  patient: number;
  appointment?: number;
  medical_record?: number;
  notes?: string;
  items: PrescriptionItemPayload[];
}

export async function createPrescription(payload: CreatePrescriptionPayload): Promise<Prescription> {
  const { data } = await api.post<Prescription>("/api/prescriptions/", payload);
  return data;
}
