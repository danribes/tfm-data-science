import { useState } from "react";
import { getTheme, toggleTheme } from "../state/theme";

export function ThemeToggle() {
  const [theme, setThemeState] = useState(getTheme());
  return (
    <button type="button" className="ps" aria-label="Cambiar tema"
      onClick={() => setThemeState(toggleTheme())}>
      {theme === "dark" ? "☀️ tema claro" : "🌙 tema oscuro"}
    </button>
  );
}
