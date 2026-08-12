import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { createStaffUser, listUsers, type StaffCreatePayload } from "../../api/auth";
import { extractErrorMessage } from "../../api/client";
import type { Role } from "../../api/types";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatDateTime } from "../../format";

const STAFF_ROLES: StaffCreatePayload["role"][] = ["doctor", "receptionist", "lab_staff", "admin"];
const EMPTY_FORM: StaffCreatePayload = {
  username: "", email: "", password: "", first_name: "", last_name: "", phone_number: "", role: "doctor",
};

function CreateStaffForm({ onCreated }: { onCreated: () => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<StaffCreatePayload>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  const update = (field: keyof StaffCreatePayload) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const createMutation = useMutation({
    mutationFn: () => createStaffUser(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setForm(EMPTY_FORM);
      onCreated();
    },
    onError: (err) => setError(extractErrorMessage(err)),
  });

  return (
    <Card title="Create staff account">
      {error && <ErrorBanner message={error} />}
      <div className="field-row">
        <label className="field">
          <span>Role</span>
          <select value={form.role} onChange={(e) => setForm((f) => ({ ...f, role: e.target.value as StaffCreatePayload["role"] }))}>
            {STAFF_ROLES.map((r) => (
              <option key={r} value={r}>
                {r.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Username</span>
          <input type="text" value={form.username} onChange={update("username")} />
        </label>
      </div>
      <div className="field-row">
        <label className="field">
          <span>First name</span>
          <input type="text" value={form.first_name} onChange={update("first_name")} />
        </label>
        <label className="field">
          <span>Last name</span>
          <input type="text" value={form.last_name} onChange={update("last_name")} />
        </label>
      </div>
      <label className="field">
        <span>Email</span>
        <input type="email" value={form.email} onChange={update("email")} />
      </label>
      <label className="field">
        <span>Temporary password</span>
        <input type="password" value={form.password} onChange={update("password")} minLength={10} />
      </label>
      <button
        className="btn btn-primary"
        disabled={!form.username || !form.email || !form.password || createMutation.isPending}
        onClick={() => createMutation.mutate()}
      >
        {createMutation.isPending ? "Creating..." : "Create account"}
      </button>
      {form.role === "doctor" && (
        <p className="muted-text">
          Creating a doctor account auto-creates a blank profile — fill in specialization/fee/department
          under Doctors afterward.
        </p>
      )}
    </Card>
  );
}

export function AdminUsersPage() {
  const [roleFilter, setRoleFilter] = useState<Role | "">("");
  const [showForm, setShowForm] = useState(false);
  const users = useQuery({ queryKey: ["users", roleFilter], queryFn: () => listUsers(roleFilter || undefined) });

  return (
    <div className="page-stack">
      <div className="page-heading-row">
        <h2 className="page-heading">Users</h2>
        <div className="quick-actions">
          <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value as Role | "")}>
            <option value="">All roles</option>
            <option value="admin">Admin</option>
            <option value="doctor">Doctor</option>
            <option value="patient">Patient</option>
            <option value="receptionist">Receptionist</option>
            <option value="lab_staff">Lab Staff</option>
          </select>
          <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
            {showForm ? "Close" : "Create staff account"}
          </button>
        </div>
      </div>

      {showForm && <CreateStaffForm onCreated={() => setShowForm(false)} />}

      <Card>
        {users.isLoading && <Spinner />}
        {users.isError && <ErrorBanner message="Could not load users." />}
        {!users.isLoading && (users.data ?? []).length === 0 && <EmptyState message="No users found." />}
        {users.data?.map((u) => (
          <div key={u.id} className="list-row list-row-bordered">
            <div>
              <div className="list-row-title">
                {u.first_name} {u.last_name} ({u.username})
              </div>
              <div className="list-row-subtitle">
                {u.email} &middot; joined {formatDateTime(u.date_joined)}
              </div>
            </div>
            <Badge tone="info">{u.role.replaceAll("_", " ")}</Badge>
          </div>
        ))}
      </Card>
    </div>
  );
}
