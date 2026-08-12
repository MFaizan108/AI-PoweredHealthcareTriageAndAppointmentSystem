import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { getQueue } from "../../api/appointments";
import { Badge, StatusBadge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatTime } from "../../format";

export function DoctorQueuePage() {
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const queue = useQuery({ queryKey: ["queue", date], queryFn: () => getQueue({ date }) });

  return (
    <div className="page-stack">
      <div className="page-heading-row">
        <h2 className="page-heading">Today's Queue</h2>
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      </div>

      <Card title="Patients">
        {queue.isLoading && <Spinner />}
        {queue.isError && <ErrorBanner message="Could not load the queue." />}
        {!queue.isLoading && (queue.data ?? []).length === 0 && <EmptyState message="No appointments for this date." />}
        {queue.data?.map((entry, i) => (
          <div key={`${entry.token_number}-${i}`} className="list-row list-row-bordered">
            <div>
              <div className="list-row-title">
                Token {entry.token_number} &middot; {entry.patient}
              </div>
              <div className="list-row-subtitle">{formatTime(entry.slot_start_time)}</div>
            </div>
            <div className="list-row-actions">
              {entry.checked_in && <Badge tone="info">Checked in</Badge>}
              <StatusBadge status={entry.status} />
            </div>
          </div>
        ))}
      </Card>
    </div>
  );
}
