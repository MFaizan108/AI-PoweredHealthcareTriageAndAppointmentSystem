import { api } from "./client";
import type { Message, Paginated } from "./types";

export async function listMessages(appointmentId: number): Promise<Message[]> {
  const { data } = await api.get<Paginated<Message> | Message[]>("/api/messages/", {
    params: { appointment: String(appointmentId) },
  });
  return Array.isArray(data) ? data : data.results;
}

export async function sendMessage(payload: { appointment: number; body: string }): Promise<Message> {
  const { data } = await api.post<Message>("/api/messages/", payload);
  return data;
}

export async function markMessageRead(id: number): Promise<Message> {
  const { data } = await api.post<Message>(`/api/messages/${id}/mark-read/`);
  return data;
}
