import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { downloadPrescriptionPdf, listPrescriptions } from "../../api/prescriptions";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatDateTime } from "../../format";

function DownloadPdfButton({ prescriptionId }: { prescriptionId: number }) {
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState(false);

  const handleDownload = async () => {
    setDownloading(true);
    setError(false);
    try {
      const blob = await downloadPrescriptionPdf(prescriptionId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `prescription_${prescriptionId}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      setError(true);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <>
      <button className="btn btn-secondary" onClick={handleDownload} disabled={downloading}>
        {downloading ? "Downloading..." : "Download PDF"}
      </button>
      {error && <ErrorBanner message="Could not download the PDF." />}
    </>
  );
}

export function PrescriptionsPage() {
  const prescriptions = useQuery({ queryKey: ["prescriptions"], queryFn: () => listPrescriptions() });

  return (
    <div className="page-stack">
      <h2 className="page-heading">Prescriptions</h2>

      {prescriptions.isLoading && <Spinner />}
      {prescriptions.isError && <ErrorBanner message="Could not load prescriptions." />}
      {!prescriptions.isLoading && (prescriptions.data ?? []).length === 0 && <EmptyState message="No prescriptions yet." />}

      {prescriptions.data?.map((p) => (
        <Card
          key={p.id}
          title={formatDateTime(p.created_at)}
          actions={<DownloadPdfButton prescriptionId={p.id} />}
        >
          <p className="muted-text">
            Prescribed by Dr. {p.doctor_detail.user.first_name} {p.doctor_detail.user.last_name}
          </p>
          {p.notes && <p>{p.notes}</p>}
          <table className="data-table">
            <thead>
              <tr>
                <th>Medicine</th>
                <th>Dosage</th>
                <th>Frequency</th>
                <th>Duration</th>
                <th>Instructions</th>
              </tr>
            </thead>
            <tbody>
              {p.items.map((item) => (
                <tr key={item.id}>
                  <td>{item.medicine_name}</td>
                  <td>{item.dosage}</td>
                  <td>{item.frequency}</td>
                  <td>{item.duration}</td>
                  <td>{item.instructions}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ))}
    </div>
  );
}
