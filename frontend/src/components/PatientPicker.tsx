import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { listPatients } from "../api/patients";
import type { Patient } from "../api/types";

export function PatientPicker({
  value,
  onChange,
}: {
  value: Patient | null;
  onChange: (patient: Patient | null) => void;
}) {
  const [search, setSearch] = useState("");
  const results = useQuery({
    queryKey: ["patient-picker", search],
    queryFn: () => listPatients({ search }),
    enabled: search.length >= 2,
  });

  if (value) {
    return (
      <div className="patient-picker-selected">
        <span>
          {value.user.first_name} {value.user.last_name} ({value.user.username})
        </span>
        <button type="button" className="link-button" onClick={() => onChange(null)}>
          Change
        </button>
      </div>
    );
  }

  return (
    <div className="patient-picker">
      <input
        placeholder="Search patient by name, username, phone..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      {search.length >= 2 && (
        <div className="patient-picker-results">
          {results.isLoading && <div className="patient-picker-item muted-text">Searching...</div>}
          {results.data?.length === 0 && <div className="patient-picker-item muted-text">No matches.</div>}
          {results.data?.map((p) => (
            <button
              type="button"
              key={p.id}
              className="patient-picker-item"
              onClick={() => {
                onChange(p);
                setSearch("");
              }}
            >
              {p.user.first_name} {p.user.last_name} ({p.user.username})
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
