import { useId, type ReactNode } from "react";

interface SelectFieldProps<T extends string | number> {
  label: string;
  value: T | null;
  options: { value: T; label: string }[];
  onChange: (value: T | null) => void;
  placeholder?: string;
  disabled?: boolean;
  hint?: ReactNode;
}

export function SelectField<T extends string | number>({
  label,
  value,
  options,
  onChange,
  placeholder,
  disabled,
  hint,
}: SelectFieldProps<T>) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <select
        id={id}
        value={value === null ? "" : String(value)}
        disabled={disabled}
        onChange={(event) => {
          const chosen = options.find((option) => String(option.value) === event.target.value);
          onChange(chosen ? chosen.value : null);
        }}
      >
        {placeholder !== undefined && <option value="">{placeholder}</option>}
        {options.map((option) => (
          <option key={String(option.value)} value={String(option.value)}>
            {option.label}
          </option>
        ))}
      </select>
      {hint && <small className="field__hint">{hint}</small>}
    </div>
  );
}

interface TextFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: "text" | "search" | "number";
  placeholder?: string;
}

export function TextField({ label, value, onChange, type = "text", placeholder }: TextFieldProps) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        type={type}
        value={value}
        placeholder={placeholder}
        inputMode={type === "number" ? "numeric" : undefined}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}
