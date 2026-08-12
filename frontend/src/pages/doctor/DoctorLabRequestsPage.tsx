import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { extractErrorMessage } from "../../api/client";
import { createLabTest, listLabTests } from "../../api/laboratory";
import type { Patient } from "../../api/types";
import { PatientPicker } from "../../components/PatientPicker";
import { StatusBadge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatDateTime } from "../../format";

function NewLabRequestForm({ onCreated }: { onCreated: () => void }) {
  const queryClient = useQueryClient();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [testName, setTestName] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: () => {
      if (!patient) throw new Error("Select a patient first.");
      return createLabTest({ patient: patient.id, test_name: testName, notes });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lab-tests"] });
      setPatient(null);
      setTestName("");
      setNotes("");
      onCreated();
    },
    onError: (err) => setError(extractErrorMessage(err)),
  });

  return (
    <Card title="Request a lab test">
      {error && <ErrorBanner message={error} />}
      <label className="field">
        <span>Patient</span>
        <PatientPicker value={patient} onChange={setPatient} />
      </label>
      <label className="field">
        <span>Test name</span>
        <input type="text" value={testName} onChange={(e) => setTestName(e.target.value)} placeholder="e.g. Complete Blood Count" />
      </label>
      <label className="field">
        <span>Notes (optional)</span>
        <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} />
      </label>
      <button
        className="btn btn-primary"
        disabled={!patient || !testName.trim() || createMutation.isPending}
        onClick={() => createMutation.mutate()}
      >
        {createMutation.isPending ? "Requesting..." : "Request test"}
      </button>
    </Card>
  );
}

export function DoctorLabRequestsPage() {
  const [showForm, setShowForm] = useState(false);
  const labTests = useQuery({ queryKey: ["lab-tests"], queryFn: () => listLabTests() });

  return (
    <div className="page-stack">
      <div className="page-heading-row">
        <h2 className="page-heading">Lab Requests</h2>
        <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Close" : "Request lab test"}
        </button>
      </div>

      {showForm && <NewLabRequestForm onCreated={() => setShowForm(false)} />}

      <Card title="Requested tests">
        {labTests.isLoading && <Spinner />}
        {labTests.isError && <ErrorBanner message="Could not load lab tests." />}
        {!labTests.isLoading && (labTests.data ?? []).length === 0 && <EmptyState message="No lab tests requested yet." />}
        {labTests.data?.map((t) => (
          <div key={t.id} className="list-row list-row-bordered">
            <div>
              <div className="list-row-title">
                {t.test_name} &middot; {t.patient_detail.user.first_name} {t.patient_detail.user.last_name}
              </div>
              <div className="list-row-subtitle">{formatDateTime(t.requested_at)}</div>
              {t.report?.result_summary && <div className="list-row-meta">{t.report.result_summary}</div>}
            </div>
            <StatusBadge status={t.status} />
          </div>
        ))}
      </Card>
    </div>
  );
}
