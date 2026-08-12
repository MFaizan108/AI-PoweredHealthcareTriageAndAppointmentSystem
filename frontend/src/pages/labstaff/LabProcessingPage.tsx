import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { extractErrorMessage } from "../../api/client";
import { listLabTests, updateLabTestStatus, uploadLabReport } from "../../api/laboratory";
import type { LabTest } from "../../api/types";
import { StatusBadge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatDateTime } from "../../format";

function UploadReportForm({ test, onDone }: { test: LabTest; onDone: () => void }) {
  const queryClient = useQueryClient();
  const [summary, setSummary] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const uploadMutation = useMutation({
    mutationFn: () => uploadLabReport({ lab_test: test.id, result_summary: summary, file: file ?? undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lab-tests"] });
      onDone();
    },
    onError: (err) => setError(extractErrorMessage(err)),
  });

  return (
    <div className="report-block">
      {error && <ErrorBanner message={error} />}
      <label className="field">
        <span>Result summary</span>
        <textarea value={summary} onChange={(e) => setSummary(e.target.value)} rows={2} />
      </label>
      <label className="field">
        <span>Report file (PDF/JPG/PNG, optional)</span>
        <input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      </label>
      <button
        className="btn btn-primary"
        disabled={!summary.trim() || uploadMutation.isPending}
        onClick={() => uploadMutation.mutate()}
      >
        {uploadMutation.isPending ? "Uploading..." : "Upload report"}
      </button>
    </div>
  );
}

export function LabProcessingPage() {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [uploadingFor, setUploadingFor] = useState<number | null>(null);

  const collected = useQuery({ queryKey: ["lab-tests", "sample_collected"], queryFn: () => listLabTests({ status: "sample_collected" }) });
  const processing = useQuery({ queryKey: ["lab-tests", "processing"], queryFn: () => listLabTests({ status: "processing" }) });

  const startProcessingMutation = useMutation({
    mutationFn: (id: number) => updateLabTestStatus(id, "processing"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["lab-tests"] }),
    onError: (err) => setError(extractErrorMessage(err)),
  });

  const tests = [...(collected.data ?? []), ...(processing.data ?? [])];
  const isLoading = collected.isLoading || processing.isLoading;

  return (
    <div className="page-stack">
      <h2 className="page-heading">Processing</h2>
      {error && <ErrorBanner message={error} />}
      <Card title="In progress">
        {isLoading && <Spinner />}
        {!isLoading && tests.length === 0 && <EmptyState message="No tests currently being processed." />}
        {tests.map((t) => (
          <div key={t.id} className="list-row list-row-bordered" style={{ flexDirection: "column", alignItems: "stretch" }}>
            <div className="list-row" style={{ padding: 0 }}>
              <div>
                <div className="list-row-title">
                  {t.test_name} &middot; {t.patient_detail.user.first_name} {t.patient_detail.user.last_name}
                </div>
                <div className="list-row-subtitle">{formatDateTime(t.requested_at)}</div>
              </div>
              <div className="list-row-actions">
                <StatusBadge status={t.status} />
                {t.status === "sample_collected" && (
                  <button className="btn btn-ghost" disabled={startProcessingMutation.isPending} onClick={() => startProcessingMutation.mutate(t.id)}>
                    Start processing
                  </button>
                )}
                <button className="btn btn-secondary" onClick={() => setUploadingFor(uploadingFor === t.id ? null : t.id)}>
                  {uploadingFor === t.id ? "Cancel" : "Upload report"}
                </button>
              </div>
            </div>
            {uploadingFor === t.id && <UploadReportForm test={t} onDone={() => setUploadingFor(null)} />}
          </div>
        ))}
      </Card>
    </div>
  );
}
