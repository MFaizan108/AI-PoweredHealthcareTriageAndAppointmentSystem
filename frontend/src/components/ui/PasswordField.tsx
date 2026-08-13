import { useId, useState, type ChangeEvent } from "react";

export function PasswordField({
  label,
  value,
  onChange,
  autoComplete,
  minLength,
  required,
  disabled,
}: {
  label: string;
  value: string;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  autoComplete?: string;
  minLength?: number;
  required?: boolean;
  disabled?: boolean;
}) {
  const [visible, setVisible] = useState(false);
  const id = useId();

  return (
    <div className="field">
      <label htmlFor={id}>
        <span>{label}</span>
      </label>
      <div className="password-field">
        <input
          id={id}
          type={visible ? "text" : "password"}
          value={value}
          onChange={onChange}
          autoComplete={autoComplete}
          minLength={minLength}
          required={required}
          disabled={disabled}
        />
        <button
          type="button"
          className="password-toggle"
          onClick={() => setVisible((v) => !v)}
          tabIndex={-1}
          disabled={disabled}
          aria-label={visible ? "Hide password" : "Show password"}
        >
          {visible ? "Hide" : "Show"}
        </button>
      </div>
    </div>
  );
}
