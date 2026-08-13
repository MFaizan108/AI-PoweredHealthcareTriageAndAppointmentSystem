import { useQuery } from "@tanstack/react-query";
import { listAppointments } from "../../api/appointments";
import { listMedicalRecords } from "../../api/medicalRecords";
import { listPrescriptions } from "../../api/prescriptions";
import { Card } from "../../components/ui/Card";
import { Spinner } from "../../components/ui/Spinner";
import { StatCard } from "../../components/ui/StatCard";

/** Admin-only analytics endpoints (/api/analytics/*) aren't reachable by a doctor account — this
 * derives a lightweight "my activity" summary client-side from the doctor's own already-scoped
 * data instead, rather than requesting a backend permission change out of scope for this phase. */
export function DoctorActivityPage() {
  const appointments = useQuery({ queryKey: ["appointments"], queryFn: () => listAppointments() });
  const records = useQuery({ queryKey: ["medical-records"], queryFn: () => listMedicalRecords() });
  const prescriptions = useQuery({ queryKey: ["prescriptions"], queryFn: () => listPrescriptions() });

  const isLoading = appointments.isLoading || records.isLoading || prescriptions.isLoading;

  const byStatus = (appointments.data ?? []).reduce<Record<string, number>>((acc, a) => {
    acc[a.status] = (acc[a.status] ?? 0) + 1;
    return acc;
  }, {});

  const uniquePatients = new Set((appointments.data ?? []).map((a) => a.patient)).size;

  return (
    <div className="page-stack">
      <h2 className="page-heading">My Activity</h2>

      {isLoading ? (
        <Spinner />
      ) : (
        <>
          <div className="stat-grid">
            <StatCard icon="📅" label="Total appointments" value={appointments.data?.length ?? 0} />
            <StatCard icon="🧑‍🤝‍🧑" tone="accent" label="Unique patients seen" value={uniquePatients} />
            <StatCard icon="📋" tone="success" label="Medical records written" value={records.data?.length ?? 0} />
            <StatCard icon="💊" tone="warning" label="Prescriptions issued" value={prescriptions.data?.length ?? 0} />
          </div>

          <Card title="Appointments by status">
            <table className="data-table">
              <tbody>
                {Object.entries(byStatus).map(([status, count]) => (
                  <tr key={status}>
                    <td style={{ textTransform: "capitalize" }}>{status.replaceAll("_", " ")}</td>
                    <td>{count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      )}
    </div>
  );
}
