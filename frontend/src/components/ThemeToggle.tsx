import { useState } from "react";
import { cycleTheme, getPref, type Pref } from "../state/theme";

/** Tres estados y no dos, porque «seguir al sistema» es una elección.
 *
 *  Con sólo claro/oscuro, el primer clic dejaba una preferencia fija y el
 *  lector no tenía forma de volver a que la página siguiera a su sistema.
 */
const LABEL: Record<Pref, string> = {
  system: "🖥️ tema del sistema",
  light: "☀️ tema claro",
  dark: "🌙 tema oscuro",
};

export function ThemeToggle() {
  const [pref, setPrefState] = useState<Pref>(getPref());
  return (
    <button type="button" className="ps" aria-label="Cambiar tema"
      title="Alterna entre seguir al sistema, claro y oscuro"
      onClick={() => setPrefState(cycleTheme())}>
      {LABEL[pref]}
    </button>
  );
}
