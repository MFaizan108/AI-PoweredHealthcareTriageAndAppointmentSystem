import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register } from "../../api/auth";
import { extractErrorMessage } from "../../api/client";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { PasswordField } from "../../components/ui/PasswordField";

function AuthVisual() {
  return (
    <div className="auth-visual" aria-hidden="true">
      <div className="auth-visual-brand">
        <span className="auth-visual-mark">+</span>
        Healthcare Triage
      </div>
      <h2 className="auth-visual-title">One connected platform for triage, appointments, and care.</h2>
      <p className="auth-visual-subtitle">
        A deterministic rule engine decides urgency — an AI assistant only explains the decision, never makes it.
      </p>
      <div className="auth-visual-features">
        <div className="auth-visual-feature">
          <span className="auth-visual-feature-icon">🩺</span>
          Symptom triage with red-flag detection and a suggested department
        </div>
        <div className="auth-visual-feature">
          <span className="auth-visual-feature-icon">📅</span>
          Book against a doctor's real availability — no double-booking
        </div>
        <div className="auth-visual-feature">
          <span className="auth-visual-feature-icon">🔒</span>
          Role-based access, 2FA, and a full audit trail on every record
        </div>
      </div>
    </div>
  );
}

export function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", email: "", password: "", first_name: "", last_name: "" });
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const update = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(form);
      setDone(true);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (done) {
    return (
      <div className="auth-page">
        <AuthVisual />
        <div className="auth-form-panel">
          <div className="auth-card" style={{ textAlign: "center" }}>
            <h1 className="auth-title">Check your email</h1>
            <p className="auth-subtitle">
              Account created. We sent a verification link to {form.email}. You can sign in now.
            </p>
            <button className="btn btn-primary" onClick={() => navigate("/login")}>
              Go to sign in
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <AuthVisual />
      <div className="auth-form-panel">
        <form className="auth-card" onSubmit={handleSubmit}>
          <h1 className="auth-title">Create your account</h1>
          <p className="auth-subtitle">Patient registration</p>

          {error && <ErrorBanner message={error} />}

          <div className="field-row">
            <label className="field">
              <span>First name</span>
              <input type="text" value={form.first_name} onChange={update("first_name")} required />
            </label>
            <label className="field">
              <span>Last name</span>
              <input type="text" value={form.last_name} onChange={update("last_name")} required />
            </label>
          </div>
          <label className="field">
            <span>Username</span>
            <input type="text" value={form.username} onChange={update("username")} autoComplete="username" required />
          </label>
          <label className="field">
            <span>Email</span>
            <input type="email" value={form.email} onChange={update("email")} autoComplete="email" required />
          </label>
          <PasswordField
            label="Password"
            value={form.password}
            onChange={update("password")}
            autoComplete="new-password"
            minLength={10}
            required
          />

          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Creating account..." : "Create account"}
          </button>

          <p className="auth-footer">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
