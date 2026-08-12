import { useQuery } from "@tanstack/react-query";
import { listLabTests } from "../../api/laboratory";
import { StatusBadge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatDateTime } from "../../format";

export function LabReportsPage() {
  const labTests = useQuery({ queryKey: ["lab-tests"], queryFn: () => listLabTests() });

  return (
    <div className="page-stack">
      <h2 className="page-heading">Lab Tests &amp; Reports</h2>

      {labTests.isLoading && <Spinner />}
      {labTests.isError && <ErrorBanner message="Could not load lab tests." />}
      {!labTests.isLoading && (labTests.data ?? []).length === 0 && <EmptyState message="No lab tests requested yet." />}

      {labTests.data?.map((t) => (
        <Card key={t.id} title={t.test_name} actions={<StatusBadge status={t.status} />}>
          <p className="muted-text">
            Requested by Dr. {t.requested_by_detail.user.first_name} {t.requested_by_detail.user.last_name} on{" "}
            {formatDateTime(t.requested_at)}
          </p>
          {t.notes && <p>{t.notes}</p>}
          {t.report ? (
            <div className="report-block">
              {t.report.result_summary && <p>{t.report.result_summary}</p>}
              {t.report.report_file && (
                <a className="btn btn-secondary" href={t.report.report_file} target="_blank" rel="noreferrer">
                  View report file
                </a>
              )}
              {t.report.reviewed_by_doctor && <p className="muted-text">Reviewed by doctor.</p>}
            </div>
          ) : (
            <p className="muted-text">Report not yet available.</p>
          )}
        </Card>
      ))}
    </div>
  );
}
