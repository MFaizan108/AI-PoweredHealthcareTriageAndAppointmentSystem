import { api } from "./client";
import type { Department, Paginated } from "./types";

export async function listDepartments(): Promise<Department[]> {
  const { data } = await api.get<Paginated<Department> | Department[]>("/api/departments/");
  return Array.isArray(data) ? data : data.results;
}

export async function createDepartment(payload: { name: string; description?: string }): Promise<Department> {
  const { data } = await api.post<Department>("/api/departments/", payload);
  return data;
}

export async function updateDepartment(id: number, payload: Partial<Department>): Promise<Department> {
  const { data } = await api.patch<Department>(`/api/departments/${id}/`, payload);
  return data;
}
