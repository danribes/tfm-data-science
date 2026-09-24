import { SERIES_FORMAT } from "../components/KpiRow";
import { cambio, cap, leverSpoken, nivel, parte, spoken, v } from "./hablado";
import { outcomeFor, sorna } from "./sorna";

/** «Y en corto»: the answer told the way you would tell a friend, ending on
 *  the ironic line.
 *
 *  Built here from the numbers already on screen rather than asked of the
 *  model, so every figure in it is the one in the headline, the chart and the
 *  companion — a colloquial paragraph that disagreed with the chart above it
 *  would be the worst kind of friendly. The order is fixed: what happens, where
 *  it stands today, who pushes it, what the companion does, the caveat, and
 *  the joke last.
 *
 *  Spoken, not printed: no quotation marks, no brackets and no exact
 *  decimals — «el saldo público apenas se mueve y se queda en un déficit de
 *  cerca del 15 % del PIB». The exact figures are right above it. */
export interface EnCortoInput {
  persona?: string;
  series: string;
  companion?: string;
  /** Scenario and base values of the series at the answer year. */
  value: number;
  baseValue: number;
  /** Base value at the first year: where the figure stands today. */
  today: number;
  year: number;
  firstYear: number;
  companionValue?: number;
  companionBase?: number;
  /** Single-lever breakdown from /explain, when it has arrived. */
  contributions?: { lever_id?: string; lever_name: string; delta: number; share: number }[];
  /** Whether any lever is away from its base value. */
  moved: boolean;
}

export function enCorto(i: EnCortoInput): string {
  const dec = SERIES_FORMAT[i.series]?.dec ?? 1;
  const np = spoken(i.series).np;
  const delta = i.value - i.baseValue;
  const outcome = outcomeFor(i.persona ?? "", i.series, delta, dec);
  const queda = v(i.series, "se queda", "se quedan");
  const parts: string[] = [];

  if (!i.moved) {
    parts.push(`Resumiendo: sin tocar ninguna palanca, en ${i.year} ${np} ${queda} ` +
      `${nivel(i.series, i.value)}, que es lo que sale de los datos de partida.`);
  } else if (outcome === "igual") {
    parts.push(`Resumiendo: con las palancas como las has dejado, en ${i.year} ${np} ${queda} ` +
      `${nivel(i.series, i.value)}, prácticamente lo mismo que sin tocar nada.`);
  } else {
    const verb = delta > 0 ? v(i.series, "sube", "suben") : v(i.series, "baja", "bajan");
    const verdict = i.persona
      ? `, y eso, para ti, es ${outcome === "mejor" ? "buena" : "mala"} noticia`
      : "";
    parts.push(`Resumiendo: con las palancas como las has dejado, ${np} ${verb} y en ${i.year} ${queda} ` +
      `${nivel(i.series, i.value)}, ${cambio(i.series, delta)} ` +
      `${delta > 0 ? "más" : "menos"} que si no tocaras nada${verdict}.`);
  }

  // An index is 100 in the first year by construction: «hoy está igual que
  // en 2026» would say nothing.
  if (i.year > i.firstYear && (SERIES_FORMAT[i.series]?.unit ?? "") !== "") {
    parts.push(`Para situarte, hoy ${v(i.series, "está", "están")} ${nivel(i.series, i.today)}.`);
  }

  if (i.moved && i.contributions && i.contributions.length > 0) {
    const movers = [...i.contributions]
      .filter((c) => Math.abs(c.delta) >= 0.5 * 10 ** -dec)
      .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
    if (movers.length === 0) {
      parts.push("Ninguna de las palancas que has movido llega de verdad a esta cifra.");
    } else {
      const [top, second] = movers;
      const who = leverSpoken(top.lever_id ?? "", top.lever_name);
      const plural = /^(los|las) /.test(who);
      const next = second ? leverSpoken(second.lever_id ?? "", second.lever_name) : "";
      parts.push(`Lo que más empuja ${plural ? "son" : "es"} ${who}, que ${plural ? "explican" : "explica"} ` +
        `${parte(top.share)}${next ? `, y le ${/^(los|las) /.test(next) ? "siguen" : "sigue"} ${next}` : ""}.`);
    }
  }

  if (i.companion && i.companionValue !== undefined && i.companionBase !== undefined) {
    const cdec = SERIES_FORMAT[i.companion]?.dec ?? 1;
    const cd = i.companionValue - i.companionBase;
    const cnp = spoken(i.companion).np;
    const cqueda = v(i.companion, "se queda", "se quedan");
    const where = nivel(i.companion, i.companionValue);
    parts.push(Math.abs(cd) < 0.5 * 10 ** -cdec
      ? `Para ponerlo en contexto, ${cnp} apenas ${v(i.companion, "se mueve", "se mueven")} y ${cqueda} ${where}.`
      : `Para ponerlo en contexto, ${cnp} ${cd > 0 ? v(i.companion, "sube", "suben") : v(i.companion, "baja", "bajan")} ` +
        `y ${cqueda} ${where}.`);
  }

  parts.push("Todo esto, claro, si esos supuestos se mantuvieran: es un escenario, no una bola de cristal.");

  const joke = sorna(i.persona, i.series, delta, dec, i.year);
  if (joke) parts.push(joke);
  return parts.map((s, k) => (k === 0 ? s : cap(s))).join(" ");
}
