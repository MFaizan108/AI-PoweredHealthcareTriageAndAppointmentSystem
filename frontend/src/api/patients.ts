import { api } from "./client";
import type { Paginated, Patient } from "./types";

export async function listPatients(params?: Record<string, string>): Promise<Patient[]> {
  const { data } = await api.get<Paginated<Patient> | Patient[]>("/api/patients/", { params });
  return Array.isArray(data) ? data : data.results;
}

export async function searchPatients(search: string): Promise<Patient[]> {
  return listPatients({ search });
}
