import type { ReactNode } from "react";

export type StatTone = "primary" | "accent" | "success" | "warning" | "danger";

export function StatCard({
  icon,
  label,
  value,
  tone = "primary",
}: {
  icon: string;
  label: string;
  value: ReactNode;
  tone?: StatTone;
}) {
  return (
    <div className={`stat-card${tone !== "primary" ? ` stat-card-${tone}` : ""}`}>
      <span className="stat-card-icon" aria-hidden="true">
        {icon}
      </span>
      <div className="stat-card-body">
        <div className="stat-card-label">{label}</div>
        <div className="stat-card-value">{value}</div>
      </div>
    </div>
  );
}
