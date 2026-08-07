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
