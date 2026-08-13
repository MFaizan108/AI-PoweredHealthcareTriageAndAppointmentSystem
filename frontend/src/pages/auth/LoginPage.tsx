import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { is2FARequiredError } from "../../api/auth";
import { extractErrorMessage } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { PasswordField } from "../../components/ui/PasswordField";
import { landingPathForRole } from "../../roleRouting";

function AuthVisual() {
  return (
    <div className="auth-visual" aria-hidden="true">
      <div className="auth-visual-brand">
        <span className="auth-visual-mark">+</span>
        Healthcare Triage
      </div>
      <h2 className="auth-visual-title">Care decisions, backed by a rule engine you can audit.</h2>
      <p className="auth-visual-subtitle">
        Sign in to your dashboard — triage, appointments, records, prescriptions, lab reports, billing, and
        messaging, scoped to exactly what your role can see.
      </p>
      <div className="auth-visual-features">
        <div className="auth-visual-feature">
          <span className="auth-visual-feature-icon">🩺</span>
          Rule-based triage — the LLM only explains the result, never decides it
        </div>
        <div className="auth-visual-feature">
          <span className="auth-visual-feature-icon">🛡️</span>
          2FA, rate limiting, and a full audit trail on every action
        </div>
        <div className="auth-visual-feature">
          <span className="auth-visual-feature-icon">📊</span>
          Role dashboards for patients, doctors, staff, and admins
        </div>
      </div>
    </div>
  );
}

export function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [needs2FA, setNeeds2FA] = useState(false);
  const [use2FARecoveryCode, setUse2FARecoveryCode] = useState(false);
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) {
    const from = (location.state as { from?: string } | null)?.from;
    return <Navigate to={from ?? landingPathForRole(user.role)} replace />;
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const freshUser = await login({
        username,
        password,
        ...(needs2FA && use2FARecoveryCode ? { recovery_code: code } : {}),
        ...(needs2FA && !use2FARecoveryCode ? { otp_code: code } : {}),
      });
      const from = (location.state as { from?: string } | null)?.from;
      navigate(from ?? landingPathForRole(freshUser.role), { replace: true });
    } catch (err) {
      if (is2FARequiredError(err)) {
        setNeeds2FA(true);
        setError("This account has 2FA enabled. Enter your authenticator code below.");
      } else {
        setError(extractErrorMessage(err));
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <AuthVisual />
      <div className="auth-form-panel">
        <form className="auth-card" onSubmit={handleSubmit}>
          <h1 className="auth-title">Healthcare Triage &amp; Appointment System</h1>
          <p className="auth-subtitle">Sign in to continue</p>

          {error && <ErrorBanner message={error} tone={needs2FA ? "info" : "danger"} />}

          <label className="field">
            <span>Username</span>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
              disabled={needs2FA}
            />
          </label>
          <PasswordField
            label="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
            disabled={needs2FA}
          />

          {needs2FA && (
            <label className="field">
              <span>{use2FARecoveryCode ? "Recovery code" : "Authenticator code"}</span>
              <input
                value={code}
                onChange={(e) => setCode(e.target.value)}
                autoComplete="one-time-code"
                placeholder={use2FARecoveryCode ? "XXXXXXXX-XXXXXXXX" : "123456"}
                required
                autoFocus
              />
              <button
                type="button"
                className="link-button"
                onClick={() => {
                  setUse2FARecoveryCode((v) => !v);
                  setCode("");
                }}
              >
                {use2FARecoveryCode ? "Use authenticator code instead" : "Lost your device? Use a recovery code"}
              </button>
            </label>
          )}

          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Signing in..." : "Sign in"}
          </button>

          <p className="auth-footer">
            New patient? <Link to="/register">Create an account</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
