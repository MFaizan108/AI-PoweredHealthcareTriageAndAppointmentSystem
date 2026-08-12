import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { listAuditLogs } from "../../api/auditLogs";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatDateTime } from "../../format";

export function AdminAuditLogsPage() {
  const [action, setAction] = useState("");
  const [method, setMethod] = useState("");
  const [page, setPage] = useState(1);

  const params: Record<string, string> = { page: String(page) };
  if (action) params.action = action;
  if (method) params.method = method;

  const logs = useQuery({ queryKey: ["audit-logs", action, method, page], queryFn: () => listAuditLogs(params) });

  return (
    <div className="page-stack">
      <div className="page-heading-row">
        <h2 className="page-heading">Audit Logs</h2>
        <div className="quick-actions">
          <select value={action} onChange={(e) => { setAction(e.target.value); setPage(1); }}>
            <option value="">All actions</option>
            <option value="login_success">Login success</option>
            <option value="login_failed">Login failed</option>
            <option value="create">Create</option>
            <option value="update">Update</option>
            <option value="delete">Delete</option>
          </select>
          <select value={method} onChange={(e) => { setMethod(e.target.value); setPage(1); }}>
            <option value="">All methods</option>
            <option value="POST">POST</option>
            <option value="PUT">PUT</option>
            <option value="PATCH">PATCH</option>
            <option value="DELETE">DELETE</option>
          </select>
        </div>
      </div>

      <Card>
        {logs.isLoading && <Spinner />}
        {logs.isError && <ErrorBanner message="Could not load audit logs." />}
        {!logs.isLoading && (logs.data?.results ?? []).length === 0 && <EmptyState message="No matching audit log entries." />}
        {logs.data?.results.map((entry) => (
          <div key={entry.id} className="list-row list-row-bordered">
            <div>
              <div className="list-row-title">
                {entry.method} {entry.path}
              </div>
              <div className="list-row-subtitle">
                {entry.username || entry.username_attempted || "anonymous"} &middot; {entry.action} &middot;{" "}
                {formatDateTime(entry.created_at)} &middot; {entry.ip_address ?? "unknown IP"}
              </div>
            </div>
            <span className="muted-text">{entry.status_code ?? "-"}</span>
          </div>
        ))}
      </Card>

      {logs.data && (logs.data.next || logs.data.previous) && (
        <div className="quick-actions">
          <button className="btn btn-ghost" disabled={!logs.data.previous} onClick={() => setPage((p) => Math.max(1, p - 1))}>
            Previous
          </button>
          <button className="btn btn-ghost" disabled={!logs.data.next} onClick={() => setPage((p) => p + 1)}>
            Next
          </button>
        </div>
      )}
    </div>
  );
}
