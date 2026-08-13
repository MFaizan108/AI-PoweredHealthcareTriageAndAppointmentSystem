import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { registerPatientByStaff } from "../../api/auth";
import { extractErrorMessage } from "../../api/client";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";

const EMPTY_FORM = { username: "", email: "", password: "", first_name: "", last_name: "", phone_number: "" };

export function WalkInRegistrationPage() {
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<string | null>(null);

  const update = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const registerMutation = useMutation({
    mutationFn: () => registerPatientByStaff(form),
    onSuccess: (user) => {
      setCreated(user.username);
      setForm(EMPTY_FORM);
      setError(null);
    },
    onError: (err) => setError(extractErrorMessage(err)),
  });

  return (
    <div className="page-stack">
      <h2 className="page-heading">Walk-in Registration</h2>
      <Card title="Register a new patient">
        {created && (
          <ErrorBanner tone="success" message={`Patient account "${created}" created. They can now be booked an appointment.`} />
        )}
        {error && <ErrorBanner message={error} />}

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
          <span>Username</span>
          <input type="text" value={form.username} onChange={update("username")} />
        </label>
        <label className="field">
          <span>Email</span>
          <input type="email" value={form.email} onChange={update("email")} />
        </label>
        <label className="field">
          <span>Phone number</span>
          <input type="text" value={form.phone_number} onChange={update("phone_number")} />
        </label>
        <label className="field">
          <span>Temporary password</span>
          <input type="password" value={form.password} onChange={update("password")} minLength={10} />
        </label>

        <button
          className="btn btn-primary"
          disabled={!form.username || !form.email || !form.password || registerMutation.isPending}
          onClick={() => registerMutation.mutate()}
        >
          {registerMutation.isPending ? "Registering..." : "Register patient"}
        </button>
      </Card>
    </div>
  );
}
