import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { extractErrorMessage } from "../../api/client";
import { createPrescription, listPrescriptions, type PrescriptionItemPayload } from "../../api/prescriptions";
import type { Patient } from "../../api/types";
import { PatientPicker } from "../../components/PatientPicker";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatDateTime } from "../../format";

const EMPTY_ITEM: PrescriptionItemPayload = { medicine_name: "", dosage: "", frequency: "", duration: "", instructions: "" };

function NewPrescriptionForm({ onCreated }: { onCreated: () => void }) {
  const queryClient = useQueryClient();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [notes, setNotes] = useState("");
  const [items, setItems] = useState<PrescriptionItemPayload[]>([{ ...EMPTY_ITEM }]);
  const [error, setError] = useState<string | null>(null);

  const updateItem = (index: number, field: keyof PrescriptionItemPayload, value: string) => {
    setItems((prev) => prev.map((it, i) => (i === index ? { ...it, [field]: value } : it)));
  };

  const createMutation = useMutation({
    mutationFn: () => {
      if (!patient) throw new Error("Select a patient first.");
      const validItems = items.filter((it) => it.medicine_name.trim());
      return createPrescription({ patient: patient.id, notes, items: validItems });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prescriptions"] });
      setPatient(null);
      setNotes("");
      setItems([{ ...EMPTY_ITEM }]);
      onCreated();
    },
    onError: (err) => setError(extractErrorMessage(err)),
  });

  return (
    <Card title="New prescription">
      {error && <ErrorBanner message={error} />}
      <label className="field">
        <span>Patient</span>
        <PatientPicker value={patient} onChange={setPatient} />
      </label>
      <label className="field">
        <span>Notes (optional)</span>
        <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} />
      </label>

      <h3 className="card-subtitle">Medicines</h3>
      {items.map((item, i) => (
        <div key={i} className="field-row" style={{ marginBottom: "0.5rem" }}>
          <input placeholder="Medicine" value={item.medicine_name} onChange={(e) => updateItem(i, "medicine_name", e.target.value)} />
          <input placeholder="Dosage" value={item.dosage} onChange={(e) => updateItem(i, "dosage", e.target.value)} />
          <input placeholder="Frequency" value={item.frequency} onChange={(e) => updateItem(i, "frequency", e.target.value)} />
          <input placeholder="Duration" value={item.duration} onChange={(e) => updateItem(i, "duration", e.target.value)} />
        </div>
      ))}
      <button type="button" className="link-button" onClick={() => setItems((prev) => [...prev, { ...EMPTY_ITEM }])}>
        + Add another medicine
      </button>

      <div>
        <button
          className="btn btn-primary"
          disabled={!patient || createMutation.isPending}
          onClick={() => createMutation.mutate()}
        >
          {createMutation.isPending ? "Saving..." : "Save prescription"}
        </button>
      </div>
    </Card>
  );
}

export function DoctorPrescriptionsPage() {
  const [showForm, setShowForm] = useState(false);
  const prescriptions = useQuery({ queryKey: ["prescriptions"], queryFn: () => listPrescriptions() });

  return (
    <div className="page-stack">
      <div className="page-heading-row">
        <h2 className="page-heading">Prescriptions</h2>
        <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Close" : "New prescription"}
        </button>
      </div>

      {showForm && <NewPrescriptionForm onCreated={() => setShowForm(false)} />}

      <Card title="Issued prescriptions">
        {prescriptions.isLoading && <Spinner />}
        {prescriptions.isError && <ErrorBanner message="Could not load prescriptions." />}
        {!prescriptions.isLoading && (prescriptions.data ?? []).length === 0 && <EmptyState message="No prescriptions yet." />}
        {prescriptions.data?.map((p) => (
          <div key={p.id} className="list-row list-row-bordered">
            <div>
              <div className="list-row-title">
                {p.patient_detail.user.first_name} {p.patient_detail.user.last_name}
              </div>
              <div className="list-row-subtitle">
                {formatDateTime(p.created_at)} &middot; {p.items.map((it) => it.medicine_name).join(", ")}
              </div>
            </div>
          </div>
        ))}
      </Card>
    </div>
  );
}
