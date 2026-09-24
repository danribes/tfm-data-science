/** v16 number helpers — es-ES, decimal comma, U+2212 minus. Never use toFixed in UI code. */
export function nf(v: number | null | undefined, d: number): string {
  if (v === null || v === undefined || !isFinite(v)) return "s/d";
  return new Intl.NumberFormat("es-ES", {
    minimumFractionDigits: d,
    maximumFractionDigits: d,
  })
    .format(v)
    .replace("-", "−");
}

/** Signed delta: always an explicit +/− prefix. */
export function sg(v: number, d: number): string {
  return (v >= 0 ? "+" : "−") + nf(Math.abs(v), d);
}

/** Big absolute numbers (EUR, counts): no decimals, dot thousands.
 *  useGrouping: "always" — Node's bundled ICU (77.1+) applies CLDR's
 *  minimumGroupingDigits=2 for es-ES under the default "auto", which
 *  drops the thousands separator for 1000-9999 (e.g. 1500 -> "1500"
 *  instead of "1.500"). That postdates the v16 source; eur()'s contract
 *  ("dot thousands", unconditionally) requires forcing it back on. */
export function eur(v: number): string {
  return new Intl.NumberFormat("es-ES", {
    maximumFractionDigits: 0,
    useGrouping: "always",
  })
    .format(v)
    .replace("-", "−");
}

/** Delta con signo para magnitudes grandes (€, recuentos).
 *
 *  `sg` delega en `nf`, que usa el agrupamiento "auto" de CLDR: para es-ES eso
 *  suprime el separador de millares entre 1000 y 9999. En una columna donde
 *  conviven +4.784 y +23.569 el resultado era que el primero salía "+4784" y
 *  el segundo "+23.569", como si fueran unidades distintas. `eur` ya forzaba
 *  el agrupamiento para los niveles; esto hace lo mismo con las diferencias.
 */
export function sgEur(v: number): string {
  return (v >= 0 ? "+" : "−") + eur(Math.abs(v));
}

/** La unidad de un *cambio*, que no siempre es la de la serie. Un
 *  porcentaje se mueve en puntos: de 23,4 % a 21,5 % son −1,9 puntos, y
 *  «−1,9 %» se lee como una caída relativa del 1,9 %. Una proporción del PIB
 *  se mueve en puntos de PIB. El resto conserva su unidad: un precio se mueve
 *  en euros. La misma regla que `_delta_unit` en explain/fallback.py. */
export function deltaUnit(unit: string): string {
  if (unit === "%PIB") return "puntos de PIB";
  return unit.startsWith("%") ? "puntos" : unit;
}

/** Diferencia con signo y con la unidad del cambio; los enteros (€,
 *  recuentos) con el agrupamiento de `sgEur`. Un cambio entero de ±1 dice
 *  «punto», no «puntos»: «+1 puntos» es incorrecto; «+1,0 puntos» no. */
export function sgUnit(v: number, d: number, unit: string): string {
  let u = deltaUnit(unit);
  if (d === 0 && Math.round(Math.abs(v)) === 1) u = u.replace(/^puntos\b/, "punto");
  return `${d === 0 ? sgEur(v) : sg(v, d)}${u ? ` ${u}` : ""}`;
}
