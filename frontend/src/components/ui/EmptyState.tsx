import type { ReactNode } from "react";

export function EmptyState({
  message,
  icon = "\u{1F5C2}\u{FE0F}",
  action,
}: {
  message: string;
  icon?: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <span className="empty-state-icon" aria-hidden="true">
        {icon}
      </span>
      <p className="empty-state-message">{message}</p>
      {action && <div className="empty-state-action">{action}</div>}
    </div>
  );
}
