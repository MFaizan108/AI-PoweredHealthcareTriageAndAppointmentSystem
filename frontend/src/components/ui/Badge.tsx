export type BadgeTone = "neutral" | "info" | "success" | "warning" | "danger";

const TONE_BY_STATUS: Record<string, BadgeTone> = {
  // appointments
  pending: "warning",
  confirmed: "info",
  in_consultation: "info",
  completed: "success",
  cancelled: "neutral",
  no_show: "danger",
  // triage urgency
  low: "success",
  moderate: "warning",
  high: "danger",
  emergency: "danger",
  // ai summary / lab / invoice status (shared vocabulary)
  ready: "success",
  failed: "danger",
  not_requested: "neutral",
  requested: "neutral",
  sample_collected: "info",
  processing: "info",
  unpaid: "danger",
  partially_paid: "warning",
  paid: "success",
  success: "success",
  refunded: "neutral",
  waiting: "warning",
  notified: "info",
  booked: "success",
};

export function statusTone(status: string): BadgeTone {
  return TONE_BY_STATUS[status] ?? "neutral";
}

export function Badge({ tone = "neutral", children }: { tone?: BadgeTone; children: React.ReactNode }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function StatusBadge({ status }: { status: string }) {
  return <Badge tone={statusTone(status)}>{status.replaceAll("_", " ")}</Badge>;
}
