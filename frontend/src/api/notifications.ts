import { api } from "./client";
import type { AppNotification, Paginated } from "./types";

export async function listNotifications(unreadOnly = false): Promise<AppNotification[]> {
  const { data } = await api.get<Paginated<AppNotification> | AppNotification[]>("/api/notifications/", {
    params: unreadOnly ? { unread: "1" } : undefined,
  });
  return Array.isArray(data) ? data : data.results;
}

export async function markNotificationRead(id: number): Promise<AppNotification> {
  const { data } = await api.post<AppNotification>(`/api/notifications/${id}/mark-read/`);
  return data;
}

export async function markAllNotificationsRead(): Promise<number> {
  const { data } = await api.post<{ marked_read: number }>("/api/notifications/mark-all-read/");
  return data.marked_read;
}
