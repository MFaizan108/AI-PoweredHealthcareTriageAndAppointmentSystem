import { useQuery } from "@tanstack/react-query";
import { getAIAnalytics, getAppointmentAnalytics, getPatientAnalytics } from "../../api/analytics";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { StatCard } from "../../components/ui/StatCard";

function DictTable({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data);
  if (entries.length === 0) return <p className="muted-text">No data.</p>;
  return (
    <table className="data-table">
      <tbody>
        {entries.map(([key, value]) => (
          <tr key={key}>
            <td style={{ textTransform: "capitalize" }}>{key.replaceAll("_", " ") || "Unknown"}</td>
            <td>{value}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function AdminAnalyticsPage() {
  const patientStats = useQuery({ queryKey: ["analytics", "patients"], queryFn: getPatientAnalytics });
  const appointmentStats = useQuery({ queryKey: ["analytics", "appointments"], queryFn: getAppointmentAnalytics });
  const aiStats = useQuery({ queryKey: ["analytics", "ai"], queryFn: getAIAnalytics });

  const anyError = patientStats.isError || appointmentStats.isError || aiStats.isError;
  const isLoading = patientStats.isLoading || appointmentStats.isLoading || aiStats.isLoading;

  return (
    <div className="page-stack">
      <h2 className="page-heading">AI &amp; Operational Analytics</h2>
      {isLoading && <Spinner />}
      {anyError && <ErrorBanner message="Could not load analytics." />}

      {!isLoading && !anyError && (
        <>
          <div className="stat-grid">
            <StatCard icon="🧑‍🤝‍🧑" label="Total patients" value={patientStats.data?.total_patients ?? 0} />
            <StatCard icon="🔁" tone="accent" label="Returning patients" value={patientStats.data?.returning_patients ?? 0} />
            <StatCard icon="📅" tone="success" label="Total appointments" value={appointmentStats.data?.total_appointments ?? 0} />
            <StatCard
              icon="🚨"
              tone={(aiStats.data?.emergency_escalations ?? 0) > 0 ? "danger" : "success"}
              label="Emergency escalations"
              value={aiStats.data?.emergency_escalations ?? 0}
            />
          </div>

          <Card title="Patients by gender">
            <DictTable data={patientStats.data?.gender_distribution ?? {}} />
          </Card>
          <Card title="Patients by age group">
            <DictTable data={patientStats.data?.age_distribution ?? {}} />
          </Card>
          <Card title="Department utilization">
            <DictTable data={patientStats.data?.department_utilization ?? {}} />
          </Card>
          <Card title="Appointments by status">
            <DictTable data={appointmentStats.data?.by_status ?? {}} />
          </Card>
          <Card title="Triage assessments by urgency">
            <DictTable data={aiStats.data?.by_urgency ?? {}} />
          </Card>
          <Card title="AI vs. clinician agreement">
            <p>
              {aiStats.data?.clinician_reviewed_count ?? 0} reviewed &middot;{" "}
              {aiStats.data?.ai_vs_clinician_agreement_rate_percent != null
                ? `${aiStats.data.ai_vs_clinician_agreement_rate_percent}% agreement`
                : "not enough data yet"}
            </p>
            <p className="muted-text">{aiStats.data?.note}</p>
          </Card>
        </>
      )}
    </div>
  );
}
