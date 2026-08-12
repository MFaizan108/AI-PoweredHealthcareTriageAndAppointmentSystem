import { api } from "./client";
import type { Paginated } from "./types";

export interface AuditLog {
  id: number;
  user: number | null;
  username: string;
  username_attempted: string;
  action: string;
  method: string;
  path: string;
  object_id: string;
  changes: Record<string, unknown>;
  status_code: number | null;
  ip_address: string | null;
  user_agent: string;
  created_at: string;
}

export async function listAuditLogs(params?: Record<string, string>): Promise<Paginated<AuditLog>> {
  const { data } = await api.get<Paginated<AuditLog>>("/api/audit-logs/", { params });
  return data;
}
