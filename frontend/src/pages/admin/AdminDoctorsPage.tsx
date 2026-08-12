import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { extractErrorMessage } from "../../api/client";
import { listDepartments } from "../../api/departments";
import { listDoctors, updateDoctorProfile } from "../../api/doctors";
import type { Doctor } from "../../api/types";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";

function EditDoctorForm({ doctor, onDone }: { doctor: Doctor; onDone: () => void }) {
  const queryClient = useQueryClient();
  const departments = useQuery({ queryKey: ["departments"], queryFn: listDepartments });
  const [form, setForm] = useState({
    department: doctor.department ?? "",
    specialization: doctor.specialization,
    qualification: doctor.qualification,
    license_number: doctor.license_number,
    experience_years: doctor.experience_years,
    consultation_fee: doctor.consultation_fee,
    is_active: doctor.is_active,
  });
  const [error, setError] = useState<string | null>(null);

  const updateMutation = useMutation({
    mutationFn: () =>
      updateDoctorProfile(doctor.id, {
        ...form,
        department: form.department ? Number(form.department) : null,
        experience_years: Number(form.experience_years),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["doctors"] });
      onDone();
    },
    onError: (err) => setError(extractErrorMessage(err)),
  });

  return (
    <div className="report-block">
      {error && <ErrorBanner message={error} />}
      <div className="field-row">
        <label className="field">
          <span>Department</span>
          <select value={form.department} onChange={(e) => setForm((f) => ({ ...f, department: e.target.value }))}>
            <option value="">None</option>
            {departments.data?.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Specialization</span>
          <input type="text" value={form.specialization} onChange={(e) => setForm((f) => ({ ...f, specialization: e.target.value }))} />
        </label>
      </div>
      <div className="field-row">
        <label className="field">
          <span>Qualification</span>
          <input type="text" value={form.qualification} onChange={(e) => setForm((f) => ({ ...f, qualification: e.target.value }))} />
        </label>
        <label className="field">
          <span>License number</span>
          <input type="text" value={form.license_number} onChange={(e) => setForm((f) => ({ ...f, license_number: e.target.value }))} />
        </label>
      </div>
      <div className="field-row">
        <label className="field">
          <span>Experience (years)</span>
          <input
            type="number"
            min={0}
            value={form.experience_years}
            onChange={(e) => setForm((f) => ({ ...f, experience_years: Number(e.target.value) }))}
          />
        </label>
        <label className="field">
          <span>Consultation fee</span>
          <input type="text" value={form.consultation_fee} onChange={(e) => setForm((f) => ({ ...f, consultation_fee: e.target.value }))} />
        </label>
      </div>
      <label className="checkbox-field">
        <input type="checkbox" checked={form.is_active} onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))} />
        Active (visible for booking)
      </label>
      <button className="btn btn-primary" disabled={updateMutation.isPending} onClick={() => updateMutation.mutate()}>
        {updateMutation.isPending ? "Saving..." : "Save changes"}
      </button>
    </div>
  );
}

export function AdminDoctorsPage() {
  const [editingId, setEditingId] = useState<number | null>(null);
  const doctors = useQuery({ queryKey: ["doctors", "all"], queryFn: () => listDoctors() });

  return (
    <div className="page-stack">
      <h2 className="page-heading">Doctors</h2>
      <p className="muted-text">
        New doctor accounts are created under Users (role: doctor) — a blank profile is created
        automatically; edit it here.
      </p>
      <Card>
        {doctors.isLoading && <Spinner />}
        {doctors.isError && <ErrorBanner message="Could not load doctors." />}
        {!doctors.isLoading && (doctors.data ?? []).length === 0 && <EmptyState message="No doctors yet." />}
        {doctors.data?.map((d) => (
          <div key={d.id} className="list-row list-row-bordered" style={{ flexDirection: "column", alignItems: "stretch" }}>
            <div className="list-row" style={{ padding: 0 }}>
              <div>
                <div className="list-row-title">
                  Dr. {d.user.first_name} {d.user.last_name}
                </div>
                <div className="list-row-subtitle">
                  {d.specialization || "No specialization set"} &middot; {d.department_name || "No department"} &middot; Rs{" "}
                  {d.consultation_fee}
                </div>
              </div>
              <button className="btn btn-ghost" onClick={() => setEditingId(editingId === d.id ? null : d.id)}>
                {editingId === d.id ? "Cancel" : "Edit"}
              </button>
            </div>
            {editingId === d.id && <EditDoctorForm doctor={d} onDone={() => setEditingId(null)} />}
          </div>
        ))}
      </Card>
    </div>
  );
}
