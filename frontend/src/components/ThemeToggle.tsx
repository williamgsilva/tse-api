import { useEffect, useState } from "react";

import { applyTheme, readTheme, type Theme } from "../lib/theme";

const OPTIONS: { value: Theme; icon: string; label: string }[] = [
  { value: "light", icon: "☀", label: "Tema claro" },
  { value: "system", icon: "◐", label: "Tema do sistema" },
  { value: "dark", icon: "☾", label: "Tema escuro" },
];

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(readTheme);
  useEffect(() => applyTheme(theme), [theme]);
  return (
    <div className="theme-toggle" role="group" aria-label="Tema">
      {OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={theme === option.value}
          aria-label={option.label}
          title={option.label}
          onClick={() => setTheme(option.value)}
        >
          {option.icon}
        </button>
      ))}
    </div>
  );
}
