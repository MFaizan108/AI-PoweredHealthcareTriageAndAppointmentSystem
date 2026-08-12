import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { extractErrorMessage } from "../../api/client";
import { createDepartment, listDepartments, updateDepartment } from "../../api/departments";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";

export function AdminDepartmentsPage() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);

  const departments = useQuery({ queryKey: ["departments", "all"], queryFn: listDepartments });

  const createMutation = useMutation({
    mutationFn: () => createDepartment({ name, description }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["departments"] });
      setName("");
      setDescription("");
    },
    onError: (err) => setError(extractErrorMessage(err)),
  });

  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: number; isActive: boolean }) => updateDepartment(id, { is_active: !isActive }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["departments"] }),
    onError: (err) => setError(extractErrorMessage(err)),
  });

  return (
    <div className="page-stack">
      <h2 className="page-heading">Departments</h2>

      <Card title="Add department">
        {error && <ErrorBanner message={error} />}
        <div className="field-row">
          <label className="field">
            <span>Name</span>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
          </label>
          <label className="field">
            <span>Description</span>
            <input type="text" value={description} onChange={(e) => setDescription(e.target.value)} />
          </label>
        </div>
        <button className="btn btn-primary" disabled={!name.trim() || createMutation.isPending} onClick={() => createMutation.mutate()}>
          {createMutation.isPending ? "Adding..." : "Add department"}
        </button>
      </Card>

      <Card title="All departments">
        {departments.isLoading && <Spinner />}
        {departments.isError && <ErrorBanner message="Could not load departments." />}
        {!departments.isLoading && (departments.data ?? []).length === 0 && <EmptyState message="No departments yet." />}
        {departments.data?.map((d) => (
          <div key={d.id} className="list-row list-row-bordered">
            <div>
              <div className="list-row-title">{d.name}</div>
              {d.description && <div className="list-row-subtitle">{d.description}</div>}
            </div>
            <div className="list-row-actions">
              <Badge tone={d.is_active ? "success" : "neutral"}>{d.is_active ? "Active" : "Inactive"}</Badge>
              <button
                className="btn btn-ghost"
                disabled={toggleActiveMutation.isPending}
                onClick={() => toggleActiveMutation.mutate({ id: d.id, isActive: d.is_active })}
              >
                {d.is_active ? "Deactivate" : "Activate"}
              </button>
            </div>
          </div>
        ))}
      </Card>
    </div>
  );
}
