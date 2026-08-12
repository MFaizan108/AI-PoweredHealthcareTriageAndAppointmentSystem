import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { listPatients } from "../../api/patients";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";

export function PatientsSearchPage() {
  const [search, setSearch] = useState("");
  const patients = useQuery({
    queryKey: ["patients", search],
    queryFn: () => listPatients(search ? { search } : undefined),
  });

  return (
    <div className="page-stack">
      <h2 className="page-heading">Patients</h2>
      <Card
        actions={
          <input
            placeholder="Search by name, username, phone, email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ minWidth: 260 }}
          />
        }
      >
        {patients.isLoading && <Spinner />}
        {patients.isError && <ErrorBanner message="Could not load patients." />}
        {!patients.isLoading && (patients.data ?? []).length === 0 && <EmptyState message="No patients found." />}
        {patients.data?.map((p) => (
          <div key={p.id} className="list-row list-row-bordered">
            <div>
              <div className="list-row-title">
                {p.user.first_name} {p.user.last_name} ({p.user.username})
              </div>
              <div className="list-row-subtitle">
                {p.user.email}
                {p.user.phone_number ? ` · ${p.user.phone_number}` : ""}
                {p.gender ? ` · ${p.gender}` : ""}
                {p.blood_group ? ` · ${p.blood_group}` : ""}
              </div>
              {p.known_allergies && <div className="list-row-meta">Allergies: {p.known_allergies}</div>}
            </div>
          </div>
        ))}
      </Card>
    </div>
  );
}
