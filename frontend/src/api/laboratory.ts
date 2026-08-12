import { api } from "./client";
import type { LabTest, LabTestStatus, Paginated } from "./types";

export async function listLabTests(params?: Record<string, string>): Promise<LabTest[]> {
  const { data } = await api.get<Paginated<LabTest> | LabTest[]>("/api/lab/", { params });
  return Array.isArray(data) ? data : data.results;
}

export interface CreateLabTestPayload {
  patient: number;
  appointment?: number;
  test_name: string;
  notes?: string;
}

export async function createLabTest(payload: CreateLabTestPayload): Promise<LabTest> {
  const { data } = await api.post<LabTest>("/api/lab/", payload);
  return data;
}

export async function updateLabTestStatus(id: number, status: LabTestStatus): Promise<LabTest> {
  const { data } = await api.patch<LabTest>(`/api/lab/${id}/`, { status });
  return data;
}

export async function uploadLabReport(payload: {
  lab_test: number;
  result_summary: string;
  file?: File;
}): Promise<void> {
  const form = new FormData();
  form.append("lab_test", String(payload.lab_test));
  form.append("result_summary", payload.result_summary);
  if (payload.file) form.append("report_file", payload.file);
  await api.post("/api/lab/reports/", form, { headers: { "Content-Type": "multipart/form-data" } });
}
