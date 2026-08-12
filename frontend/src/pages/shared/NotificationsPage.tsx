import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { listNotifications, markAllNotificationsRead, markNotificationRead } from "../../api/notifications";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { Spinner } from "../../components/ui/Spinner";
import { formatDateTime } from "../../format";

export function NotificationsPage() {
  const queryClient = useQueryClient();
  const [unreadOnly, setUnreadOnly] = useState(false);

  const notifications = useQuery({
    queryKey: ["notifications", unreadOnly ? "unread" : "all"],
    queryFn: () => listNotifications(unreadOnly),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["notifications"] });
  };

  const markReadMutation = useMutation({ mutationFn: markNotificationRead, onSuccess: invalidate });
  const markAllReadMutation = useMutation({ mutationFn: markAllNotificationsRead, onSuccess: invalidate });

  return (
    <div className="page-stack">
      <div className="page-heading-row">
        <h2 className="page-heading">Notifications</h2>
        <div className="quick-actions">
          <label className="checkbox-field">
            <input type="checkbox" checked={unreadOnly} onChange={(e) => setUnreadOnly(e.target.checked)} />
            Unread only
          </label>
          <button className="btn btn-secondary" onClick={() => markAllReadMutation.mutate()} disabled={markAllReadMutation.isPending}>
            Mark all read
          </button>
        </div>
      </div>

      <Card>
        {notifications.isLoading && <Spinner />}
        {!notifications.isLoading && (notifications.data ?? []).length === 0 && <EmptyState message="No notifications." />}
        {notifications.data?.map((n) => (
          <div key={n.id} className={`list-row list-row-bordered${n.is_read ? "" : " list-row-unread"}`}>
            <div>
              <div className="list-row-title">{n.title}</div>
              <div className="list-row-subtitle">{n.message}</div>
              <div className="list-row-meta">{formatDateTime(n.created_at)}</div>
            </div>
            {!n.is_read && (
              <button className="btn btn-ghost" onClick={() => markReadMutation.mutate(n.id)}>
                Mark read
              </button>
            )}
          </div>
        ))}
      </Card>
    </div>
  );
}
