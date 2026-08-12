import { useQuery } from "@tanstack/react-query";
import { listLabTests } from "../../api/laboratory";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatDateTime } from "../../format";

export function LabReportsListPage() {
  const tests = useQuery({ queryKey: ["lab-tests", "completed"], queryFn: () => listLabTests({ status: "completed" }) });

  return (
    <div className="page-stack">
      <h2 className="page-heading">Reports</h2>
      <Card title="Completed tests">
        {tests.isLoading && <Spinner />}
        {tests.isError && <ErrorBanner message="Could not load reports." />}
        {!tests.isLoading && (tests.data ?? []).length === 0 && <EmptyState message="No completed reports yet." />}
        {tests.data?.map((t) => (
          <div key={t.id} className="list-row list-row-bordered">
            <div>
              <div className="list-row-title">
                {t.test_name} &middot; {t.patient_detail.user.first_name} {t.patient_detail.user.last_name}
              </div>
              <div className="list-row-subtitle">
                Uploaded {t.report?.uploaded_at ? formatDateTime(t.report.uploaded_at) : "-"}
              </div>
              {t.report?.result_summary && <div className="list-row-meta">{t.report.result_summary}</div>}
            </div>
            {t.report?.report_file && (
              <a className="btn btn-secondary" href={t.report.report_file} target="_blank" rel="noreferrer">
                View file
              </a>
            )}
          </div>
        ))}
      </Card>
    </div>
  );
}
