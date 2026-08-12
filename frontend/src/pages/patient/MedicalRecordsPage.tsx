import { useQuery } from "@tanstack/react-query";
import { listMedicalRecords } from "../../api/medicalRecords";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatDate } from "../../format";

export function MedicalRecordsPage() {
  const records = useQuery({ queryKey: ["medical-records"], queryFn: () => listMedicalRecords() });

  return (
    <div className="page-stack">
      <h2 className="page-heading">Medical Records</h2>

      {records.isLoading && <Spinner />}
      {records.isError && <ErrorBanner message="Could not load medical records." />}
      {!records.isLoading && (records.data ?? []).length === 0 && <EmptyState message="No medical records yet." />}

      {records.data?.map((r) => (
        <Card
          key={r.id}
          title={`Visit on ${formatDate(r.visit_date)}`}
          actions={<span className="muted-text">Dr. {r.doctor_detail.user.first_name} {r.doctor_detail.user.last_name}</span>}
        >
          {r.consultation_notes && <p>{r.consultation_notes}</p>}
          {r.diagnoses.length > 0 && (
            <>
              <h3 className="card-subtitle">Diagnoses</h3>
              <ul className="plain-list">
                {r.diagnoses.map((d) => (
                  <li key={d.id}>{d.description}</li>
                ))}
              </ul>
            </>
          )}
          {r.follow_up_date && (
            <p className="muted-text">
              Follow-up recommended on {formatDate(r.follow_up_date)}
              {r.follow_up_notes ? ` — ${r.follow_up_notes}` : ""}
            </p>
          )}
        </Card>
      ))}
    </div>
  );
}
