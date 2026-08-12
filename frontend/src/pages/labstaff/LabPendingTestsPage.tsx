import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { extractErrorMessage } from "../../api/client";
import { listLabTests, updateLabTestStatus } from "../../api/laboratory";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatDateTime } from "../../format";

export function LabPendingTestsPage() {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const tests = useQuery({ queryKey: ["lab-tests", "requested"], queryFn: () => listLabTests({ status: "requested" }) });

  const collectMutation = useMutation({
    mutationFn: (id: number) => updateLabTestStatus(id, "sample_collected"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["lab-tests"] }),
    onError: (err) => setError(extractErrorMessage(err)),
  });

  return (
    <div className="page-stack">
      <h2 className="page-heading">Pending Tests</h2>
      {error && <ErrorBanner message={error} />}
      <Card title="Awaiting sample collection">
        {tests.isLoading && <Spinner />}
        {tests.isError && <ErrorBanner message="Could not load lab tests." />}
        {!tests.isLoading && (tests.data ?? []).length === 0 && <EmptyState message="No pending tests." />}
        {tests.data?.map((t) => (
          <div key={t.id} className="list-row list-row-bordered">
            <div>
              <div className="list-row-title">
                {t.test_name} &middot; {t.patient_detail.user.first_name} {t.patient_detail.user.last_name}
              </div>
              <div className="list-row-subtitle">
                Requested by Dr. {t.requested_by_detail.user.first_name} {t.requested_by_detail.user.last_name} &middot;{" "}
                {formatDateTime(t.requested_at)}
              </div>
              {t.notes && <div className="list-row-meta">{t.notes}</div>}
            </div>
            <button className="btn btn-secondary" disabled={collectMutation.isPending} onClick={() => collectMutation.mutate(t.id)}>
              Mark sample collected
            </button>
          </div>
        ))}
      </Card>
    </div>
  );
}
