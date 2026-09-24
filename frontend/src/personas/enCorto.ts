import { SERIES_FORMAT } from "../components/KpiRow";
import { nf, sgUnit } from "../lib/fmt";
import { seriesLabel } from "../lib/seriesMeta";
import { outcomeFor, sorna } from "./sorna";

/** «Y en corto»: the answer told the way you would tell a friend, ending on
 *  the ironic line.
 *
 *  Built here from the numbers already on screen rather than asked of the
 *  model, so every figure in it is the one in the headline, the chart and the
 *  companion — a colloquial paragraph that disagreed with the chart above it
 *  would be the worst kind of friendly. The order is fixed: what happens, where
 *  it stands today, who pushes it, what the companion does, the caveat, and
 *  the joke last. */
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
  contributions?: { lever_name: string; delta: number; share: number }[];
  /** Whether any lever is away from its base value. */
  moved: boolean;
}

function fmtLevel(key: string, v: number): string {
  const f = SERIES_FORMAT[key] ?? { dec: 1, unit: "" };
  return `${nf(v, f.dec)} ${f.unit}`.trim();
}

export function enCorto(i: EnCortoInput): string {
  const f = SERIES_FORMAT[i.series] ?? { dec: 1, unit: "" };
  const label = `«${seriesLabel(i.series)}»`;
  const delta = i.value - i.baseValue;
  const outcome = outcomeFor(i.persona ?? "", i.series, delta, f.dec);
  const parts: string[] = [];

  if (!i.moved) {
    parts.push(`Resumiendo: sin tocar ninguna palanca, ${label} queda en ` +
      `${fmtLevel(i.series, i.value)} en ${i.year}, que es lo que sale de los datos de partida.`);
  } else if (outcome === "igual") {
    parts.push(`Resumiendo: con las palancas como las has dejado, ${label} se queda en ` +
      `${fmtLevel(i.series, i.value)} en ${i.year}, prácticamente lo mismo que sin tocar nada.`);
  } else {
    const verb = delta > 0 ? "sube" : "baja";
    const verdict = i.persona
      ? (outcome === "mejor" ? "y eso, para ti, es buena noticia" : "y eso, para ti, es mala noticia")
      : "";
    parts.push(`Resumiendo: con las palancas como las has dejado, ${label} ${verb} hasta ` +
      `${fmtLevel(i.series, i.value)} en ${i.year}, ${sgUnit(delta, f.dec, f.unit)} frente a no ` +
      `tocar nada (que daría ${fmtLevel(i.series, i.baseValue)})${verdict ? `, ${verdict}` : ""}.`);
  }

  if (i.year > i.firstYear) {
    parts.push(`Para situarte: hoy está en ${fmtLevel(i.series, i.today)}.`);
  }

  if (i.moved && i.contributions && i.contributions.length > 0) {
    const movers = [...i.contributions]
      .filter((c) => Math.abs(c.delta) >= 0.5 * 10 ** -f.dec)
      .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
    if (movers.length === 0) {
      parts.push("Ninguna de las palancas que has movido llega de verdad a esta cifra.");
    } else {
      const [top, second] = movers;
      parts.push(`Lo que más empuja es «${top.lever_name}», con el ${nf(top.share * 100, 0)} % ` +
        `del cambio${second ? `; le sigue «${second.lever_name}»` : ""}.`);
    }
  }

  if (i.companion && i.companionValue !== undefined && i.companionBase !== undefined) {
    const cf = SERIES_FORMAT[i.companion] ?? { dec: 1, unit: "" };
    const cd = i.companionValue - i.companionBase;
    const clabel = `«${seriesLabel(i.companion)}»`;
    parts.push(Math.abs(cd) < 0.5 * 10 ** -cf.dec
      ? `Para ponerlo en contexto, ${clabel} apenas se mueve: ${fmtLevel(i.companion, i.companionValue)}.`
      : `Para ponerlo en contexto, ${clabel} queda en ${fmtLevel(i.companion, i.companionValue)} ` +
        `(${sgUnit(cd, cf.dec, cf.unit)}).`);
  }

  parts.push("Todo esto, claro, si esos supuestos se mantuvieran: es un escenario, no una bola de cristal.");

  const joke = sorna(i.persona, i.series, delta, f.dec, i.year);
  if (joke) parts.push(joke);
  return parts.join(" ");
}
