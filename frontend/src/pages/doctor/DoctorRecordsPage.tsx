import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { extractErrorMessage } from "../../api/client";
import { addDiagnosis, createMedicalRecord, listMedicalRecords } from "../../api/medicalRecords";
import type { Patient } from "../../api/types";
import { PatientPicker } from "../../components/PatientPicker";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatDate } from "../../format";

function NewRecordForm({ onCreated }: { onCreated: () => void }) {
  const queryClient = useQueryClient();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [visitDate, setVisitDate] = useState(new Date().toISOString().slice(0, 10));
  const [notes, setNotes] = useState("");
  const [diagnosisText, setDiagnosisText] = useState("");
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: async () => {
      if (!patient) throw new Error("Select a patient first.");
      const record = await createMedicalRecord({
        patient: patient.id,
        visit_date: visitDate,
        consultation_notes: notes,
      });
      if (diagnosisText.trim()) {
        await addDiagnosis(record.id, diagnosisText.trim());
      }
      return record;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["medical-records"] });
      setPatient(null);
      setNotes("");
      setDiagnosisText("");
      onCreated();
    },
    onError: (err) => setError(extractErrorMessage(err)),
  });

  return (
    <Card title="New medical record">
      {error && <ErrorBanner message={error} />}
      <label className="field">
        <span>Patient</span>
        <PatientPicker value={patient} onChange={setPatient} />
      </label>
      <label className="field">
        <span>Visit date</span>
        <input type="date" value={visitDate} onChange={(e) => setVisitDate(e.target.value)} />
      </label>
      <label className="field">
        <span>Consultation notes</span>
        <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} />
      </label>
      <label className="field">
        <span>Diagnosis (optional)</span>
        <input type="text" value={diagnosisText} onChange={(e) => setDiagnosisText(e.target.value)} />
      </label>
      <button
        className="btn btn-primary"
        disabled={!patient || createMutation.isPending}
        onClick={() => createMutation.mutate()}
      >
        {createMutation.isPending ? "Saving..." : "Save record"}
      </button>
    </Card>
  );
}

export function DoctorRecordsPage() {
  const [showForm, setShowForm] = useState(false);
  const records = useQuery({ queryKey: ["medical-records"], queryFn: () => listMedicalRecords() });

  return (
    <div className="page-stack">
      <div className="page-heading-row">
        <h2 className="page-heading">Medical Records</h2>
        <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Close" : "New record"}
        </button>
      </div>

      {showForm && <NewRecordForm onCreated={() => setShowForm(false)} />}

      <Card title="Records">
        {records.isLoading && <Spinner />}
        {records.isError && <ErrorBanner message="Could not load medical records." />}
        {!records.isLoading && (records.data ?? []).length === 0 && <EmptyState message="No medical records yet." />}
        {records.data?.map((r) => (
          <div key={r.id} className="list-row list-row-bordered">
            <div>
              <div className="list-row-title">
                {r.patient_detail.user.first_name} {r.patient_detail.user.last_name} &middot; {formatDate(r.visit_date)}
              </div>
              {r.consultation_notes && <div className="list-row-subtitle">{r.consultation_notes}</div>}
              {r.diagnoses.length > 0 && (
                <div className="list-row-meta">{r.diagnoses.map((d) => d.description).join(", ")}</div>
              )}
            </div>
          </div>
        ))}
      </Card>
    </div>
  );
}
