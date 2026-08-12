import { api } from "./client";
import type { MedicalRecord, Paginated } from "./types";

export async function listMedicalRecords(params?: Record<string, string>): Promise<MedicalRecord[]> {
  const { data } = await api.get<Paginated<MedicalRecord> | MedicalRecord[]>("/api/medical-records/", { params });
  return Array.isArray(data) ? data : data.results;
}

export async function getMedicalRecord(id: number): Promise<MedicalRecord> {
  const { data } = await api.get<MedicalRecord>(`/api/medical-records/${id}/`);
  return data;
}

export interface CreateMedicalRecordPayload {
  patient: number;
  appointment?: number;
  visit_date: string;
  consultation_notes?: string;
  follow_up_date?: string;
  follow_up_notes?: string;
}

export async function createMedicalRecord(payload: CreateMedicalRecordPayload): Promise<MedicalRecord> {
  const { data } = await api.post<MedicalRecord>("/api/medical-records/", payload);
  return data;
}

export async function addDiagnosis(medicalRecordId: number, description: string): Promise<void> {
  await api.post("/api/medical-records/diagnoses/", { medical_record: medicalRecordId, description });
}
