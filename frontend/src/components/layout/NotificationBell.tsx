import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listNotifications } from "../../api/notifications";

export function NotificationBell({ notificationsPath }: { notificationsPath: string }) {
  const { data } = useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: () => listNotifications(true),
    refetchInterval: 30_000,
  });

  const unreadCount = data?.length ?? 0;

  return (
    <Link to={notificationsPath} className="notification-bell" aria-label={`${unreadCount} unread notifications`}>
      <span aria-hidden="true">&#128276;</span>
      {unreadCount > 0 && <span className="notification-bell-badge">{unreadCount > 9 ? "9+" : unreadCount}</span>}
    </Link>
  );
}
