export type Theme = "light" | "dark" | "system";

const STORAGE = "tse-theme";

export function readTheme(): Theme {
  try {
    const stored = localStorage.getItem(STORAGE);
    return stored === "light" || stored === "dark" ? stored : "system";
  } catch {
    return "system";
  }
}

export function applyTheme(theme: Theme): void {
  const root = document.documentElement;
  if (theme === "system") root.removeAttribute("data-theme");
  else root.setAttribute("data-theme", theme);
  try {
    if (theme === "system") localStorage.removeItem(STORAGE);
    else localStorage.setItem(STORAGE, theme);
  } catch {
    // Sem armazenamento (modo privado): o tema vale só nesta visita.
  }
}
