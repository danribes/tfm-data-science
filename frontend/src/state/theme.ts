/** Tema de la interfaz: lo que el lector elige y lo que acaba aplicándose.
 *
 *  Son dos cosas distintas y confundirlas era el fallo. `Pref` es la elección
 *  —seguir al sistema, o forzar uno de los dos—; `Theme` es el que se pinta.
 *  Antes sólo existía lo segundo: se leía la preferencia del sistema una vez,
 *  al arrancar, y nunca más. Cambiar el tema del sistema con la página abierta
 *  no hacía nada, y en cuanto alguien tocaba el botón una sola vez, el valor
 *  guardado ganaba para siempre sin manera de volver a seguir al sistema.
 */
export type Theme = "light" | "dark";
export type Pref = "system" | Theme;

const KEY = "theme";

/** El orden del botón: seguir al sistema, forzar claro, forzar oscuro. */
const CYCLE: readonly Pref[] = ["system", "light", "dark"] as const;

function media(): MediaQueryList | null {
  return typeof window.matchMedia === "function"
    ? window.matchMedia("(prefers-color-scheme: dark)")
    : null;
}

function osTheme(): Theme {
  return media()?.matches ? "dark" : "light";
}

/** La preferencia guardada. Ausente significa «sigue al sistema», de modo que
 *  el valor por defecto no depende de que alguien escribiera nada. */
export function getPref(): Pref {
  const stored = localStorage.getItem(KEY);
  return stored === "light" || stored === "dark" ? stored : "system";
}

/** El tema que está pintado ahora mismo. */
export function getTheme(): Theme {
  return document.documentElement.dataset.theme === "dark" ? "dark" : "light";
}

export function resolve(pref: Pref): Theme {
  return pref === "system" ? osTheme() : pref;
}

export function setPref(pref: Pref): Theme {
  if (pref === "system") {
    localStorage.removeItem(KEY);
  } else {
    localStorage.setItem(KEY, pref);
  }
  const theme = resolve(pref);
  document.documentElement.dataset.theme = theme;
  return theme;
}

//: A qué consulta estamos suscritos, para no duplicar el oyente ni quedarnos
//: pegados al anterior. Un simple booleano bastaba en producción —se arranca
//: una vez— pero dejaba el módulo imposible de reinicializar, que es tanto un
//: problema de pruebas como una señal de que el estado estaba mal guardado.
let attached: { mql: MediaQueryList; onChange: () => void } | null = null;

export function initTheme(): void {
  document.documentElement.dataset.theme = resolve(getPref());

  const mq = media();
  if (attached?.mql === mq) return;
  attached?.mql.removeEventListener?.("change", attached.onChange);
  attached = null;
  if (!mq?.addEventListener) return;

  // Sin este oyente, cambiar el tema del sistema con la página abierta no
  // hacía nada: la preferencia se leía una vez y se olvidaba. Sólo repinta
  // mientras la elección sea «sistema»; una elección explícita manda.
  const onChange = () => {
    if (getPref() === "system") {
      document.documentElement.dataset.theme = osTheme();
    }
  };
  mq.addEventListener("change", onChange);
  attached = { mql: mq, onChange };
}

/** Avanza sistema → claro → oscuro → sistema. Devuelve la nueva preferencia. */
export function cycleTheme(): Pref {
  const next = CYCLE[(CYCLE.indexOf(getPref()) + 1) % CYCLE.length];
  setPref(next);
  return next;
}

/** Compatibilidad: el botón anterior sólo alternaba entre los dos temas. */
export function setTheme(t: Theme): void {
  setPref(t);
}

export function toggleTheme(): Theme {
  return setPref(getTheme() === "dark" ? "light" : "dark");
}
