import { SERIES_FORMAT } from "../components/KpiRow";
import { eur } from "../lib/fmt";
import { seriesLabel } from "../lib/seriesMeta";

/** The spoken register of «Y en corto»: every figure by its everyday name,
 *  with its article, and every amount rounded and said the way a person says
 *  it — «el saldo público se queda en un déficit de cerca del 15 % del
 *  PIB», not ««Saldo público» … −14,7 %PIB».
 *
 *  Only the paragraph talks like this. The headline, the charts and the
 *  technical note keep the exact figures, so nothing is lost by rounding
 *  here. */
interface Spoken { np: string; pl?: boolean }

const SPOKEN: Record<string, Spoken> = {
  b: { np: "la deuda pública" },
  u: { np: "el paro" },
  pi: { np: "la inflación" },
  saldo: { np: "el saldo público" },
  pb: { np: "el saldo primario" },
  precio: { np: "el precio de la vivienda" },
  cuota: { np: "la cuota de la hipoteca" },
  salario: { np: "el sueldo anual típico" },
  salmes: { np: "el sueldo mensual típico" },
  esf: { np: "la parte del sueldo que se va en la hipoteca" },
  arop: { np: "la pobreza infantil" },
  auton: { np: "el peso de los autónomos" },
  bono: { np: "el interés del bono a diez años" },
  spread: { np: "la prima de riesgo" },
  r: { np: "el Euríbor" },
  d1: { np: "el gasto en salarios públicos" },
  d3: { np: "las subvenciones", pl: true },
  p2: { np: "las compras corrientes del Estado", pl: true },
  p51: { np: "la inversión pública" },
  edu: { np: "el gasto en educación" },
  pens: { np: "el gasto en pensiones" },
  int: { np: "los intereses de la deuda", pl: true },
  dep: { np: "la proporción de mayores" },
  g: { np: "el crecimiento de la economía" },
  ipv: { np: "la subida del precio de la vivienda" },
  nomreal: { np: "el poder de compra de la nómina" },
  wrealIdx: { np: "el poder de compra del sueldo" },
  sobre: { np: "la sobrecarga por gastos de vivienda" },
  temp: { np: "la temporalidad" },
  ujuv: { np: "el paro de los menores de 25" },
};

const LEVER_SPOKEN: Record<string, string> = {
  r: "el Euríbor", prima: "la prima de riesgo", sp: "el ajuste del déficit",
  lam: "la productividad", pm: "el precio de la energía", tau: "los impuestos sobre el trabajo",
  z: "el marco laboral", ext: "la demanda de otros países", dem: "el envejecimiento",
  idx: "la subida de pensiones y nóminas",
};

/** Series whose value can be negative and means something different below
 *  zero: a negative balance is a deficit, a negative growth rate a fall. */
const BALANCE = new Set(["saldo", "pb"]);
const RATE = new Set(["g", "ipv", "pi", "gnom", "wreal", "wnom", "ipvreal"]);

export function spoken(key: string): Spoken {
  // Fallback: the readable name without its bracketed qualifier, lower-cased.
  return SPOKEN[key] ?? { np: `la cifra de ${seriesLabel(key).replace(/\s*\(.*?\)/g, "").toLowerCase()}` };
}

/** Capital first letter, for a noun phrase that opens a sentence. */
export const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

/** «queda» / «quedan», for a subject that may be plural. */
export const v = (key: string, sing: string, plur: string) => (spoken(key).pl ? plur : sing);

export function leverSpoken(id: string, fallback: string): string {
  return LEVER_SPOKEN[id] ?? fallback.split(" · ")[0].toLowerCase();
}

const WORDS = ["cero", "un", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez"];
const unos = (n: number) => (n === 1 ? "un" : `unos ${n <= 10 ? WORDS[n] : eur(n)}`);
// «unas dos personas» is written with WORDS too: only «un» / «una» differ.

/** «cerca del 7 %», «algo más del 1 %»: a percentage rounded to the
 *  unit, with a hedge that says which way. `de` gives the form that follows
 *  «un déficit de…». */
function pct(a: number, unit: string): string {
  const tail = unit === "%PIB" ? " % del PIB" : unit === "% a/a" ? " % al año" : " %";
  const r = Math.round(a);
  if (r === 0) return "casi cero";
  if (Math.abs(a - r) <= 0.35) return `cerca del ${r}${tail}`;
  return a > r ? `algo más del ${r}${tail}` : `algo menos del ${r}${tail}`;
}

/** Round a euro amount to a figure a person would say. */
function euros(a: number): string {
  const step = a >= 10000 ? 1000 : a >= 1000 ? 50 : 10;
  return eur(Math.round(a / step) * step);
}

/** Where a figure stands, to follow «se queda…» or «hoy está…». */
export function nivel(key: string, value: number): string {
  const unit = SERIES_FORMAT[key]?.unit ?? "";
  const a = Math.abs(value);
  if (unit.startsWith("%")) {
    if (BALANCE.has(key)) {
      return value < 0 ? `en un déficit de ${pct(a, unit)}` : `en un superávit de ${pct(a, unit)}`;
    }
    if (RATE.has(key) && value < 0) return `en una caída de ${pct(a, unit)}`;
    // «se queda cerca del 7 %», but «se queda en algo más del 1 %».
    const core = pct(a, unit);
    return core.startsWith("cerca") ? core : `en ${core}`;
  }
  if (unit.startsWith("€")) {
    const per = unit === "€/mes" ? " al mes" : unit === "€/año" ? " al año" : "";
    return `en unos ${euros(a)} euros${per}`;
  }
  if (unit === "pb") return `en unos ${eur(Math.round(a / 5) * 5)} puntos básicos`;
  if (unit === "/100") return `en unas ${Math.round(a)} personas mayores por cada cien en edad de trabajar`;
  if (unit === "") {
    // An index worth 100 in 2026. The absolute value is rounded, as in
    // `cambio`: Math.round(−17,5) is −17 but Math.round(17,5) is 18, and the
    // same change must not read 17 in one sentence and 18 in the next.
    const n = Math.round(Math.abs(value - 100));
    if (n === 0) return "prácticamente igual que en 2026";
    return `un ${n} % ${value < 100 ? "por debajo" : "por encima"} de lo que era en 2026`;
  }
  return `alrededor de ${Math.round(a)}`;
}

/** How big a change is, to follow «…» and precede «más» / «menos». */
export function cambio(key: string, delta: number): string {
  const unit = SERIES_FORMAT[key]?.unit ?? "";
  const a = Math.abs(delta);
  if (unit.startsWith("%")) {
    const pts = unit === "%PIB" ? "de PIB" : "";
    if (a < 0.3) return `unas décimas${pts ? ` ${pts}` : ""}`;
    if (a < 0.75) return `medio punto${pts ? ` ${pts}` : ""}`;
    const n = Math.round(a);
    return `${unos(n)} ${n === 1 ? "punto" : "puntos"}${pts ? ` ${pts}` : ""}`;
  }
  if (unit.startsWith("€")) return `unos ${euros(a)} euros`;
  if (unit === "pb") return `unos ${eur(Math.round(a / 5) * 5)} puntos básicos`;
  if (unit === "/100") {
    const n = Math.max(1, Math.round(a));
    return n === 1 ? "una persona mayor" : `unas ${n <= 10 ? WORDS[n] : n} personas mayores`;
  }
  const n = Math.max(1, Math.round(a));
  return `${unos(n)} ${n === 1 ? "punto" : "puntos"}`;
}

/** A lever's share of the change, in words. */
export function parte(share: number): string {
  if (share >= 0.9) return "casi todo el cambio";
  if (share >= 0.7) return "la mayor parte del cambio";
  if (share >= 0.55) return "algo más de la mitad del cambio";
  if (share >= 0.45) return "más o menos la mitad del cambio";
  if (share >= 0.3) return "alrededor de un tercio del cambio";
  if (share >= 0.2) return "alrededor de una cuarta parte del cambio";
  return "una parte pequeña del cambio";
}
