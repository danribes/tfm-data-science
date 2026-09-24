import type { Scenario } from "../engine/spain";
import { baseline, YEARS } from "../engine/spain";
import { statusOf, type RedLineDef } from "../engine/redlines";
import { GTOT_RECORD, INT_RECORD } from "../lib/historico";
import { nf } from "../lib/fmt";
import { HowToRead } from "./HowToRead";

/** «¿Cuándo es demasiada deuda?»: what the app does and does not judge, and
 *  the year each alarm goes off in the reader's own scenario.
 *
 *  The app gives no verdict on whether the debt can be paid — no model can,
 *  it depends on markets and governments — and says so first. What it has
 *  are thresholds anchored to episodes that happened, and two signals. Each
 *  row here is computed from the scenario on screen, year by year, with the
 *  same rule as the traffic light (statusOf): the alarm goes off the first
 *  year the figure passes its threshold. */
const DEBT_LINES = ["deuda_105", "deuda_120", "deficit_maastricht", "deficit_record_2012", "bono_rescate"];
/** The rest of the app's own red lines: households and the economy. */
const OTHER_LINES = ["paro_record", "inflacion_10", "esfuerzo_40", "pobreza_infantil_30"];

/** Why each threshold is where it is, said plainly. The API's own `source`
 *  string stays available as the technical note. */
const WHY: Record<string, string> = {
  deuda_105: "Un comentarista lo citó como nivel preocupante; no es un límite legal.",
  deuda_120: "Es el pico de la pandemia: el 119,3 % del PIB en 2020.",
  deficit_maastricht: "Es la regla europea: por encima abre un procedimiento de déficit excesivo.",
  deficit_record_2012: "Es el peor año registrado en España: 2012, con el rescate bancario.",
  bono_rescate: "Grecia, Portugal e Irlanda pidieron el rescate con el bono cerca del 7 %; España tocó el 7,6 % en 2012.",
  paro_record: "Es el máximo histórico de España, a principios de 2013.",
  inflacion_10: "Es la ola de 2022: la inflación de España pasó del 10 % en verano.",
  esfuerzo_40: "Es el umbral con el que Eurostat define la sobrecarga por vivienda.",
  pobreza_infantil_30: "Es el nivel de los peores años, tras 2013: el 30,1 % de 2014.",
};

type When = { kind: "hoy" } | { kind: "palancas" } | { kind: "desde"; year: number } | { kind: "nunca" };

/** The first year a series passes its threshold. «Hoy» only when the base
 *  scenario is past it in the first year too: a lever such as the Euríbor or
 *  the risk premium moves the first year straight away, and saying «ya
 *  cruzada hoy» for that would read as Spain already being above the line. */
function firstCrossing(values: number[], base: number[], threshold: number, cmp: "gt" | "lt"): When {
  const k = values.findIndex((v) => statusOf(v, threshold, cmp) === "crossed");
  if (k < 0) return { kind: "nunca" };
  if (k > 0) return { kind: "desde", year: YEARS[k] };
  return statusOf(base[0], threshold, cmp) === "crossed" ? { kind: "hoy" } : { kind: "palancas" };
}

function whenText(w: When): string {
  if (w.kind === "hoy") return "ya cruzada hoy";
  if (w.kind === "palancas") return `salta en ${YEARS[0]}, por tus palancas`;
  if (w.kind === "desde") return `salta en ${w.year}`;
  return `no salta antes de ${YEARS[YEARS.length - 1]}`;
}

export function DebtAlarms({ scn, defs }: { scn: Scenario; defs: RedLineDef[] }) {
  const base = baseline() as Record<string, number[]>;
  const bono = defs.find((d) => d.id === "bono_rescate");
  // The bond has no path of its own in this engine — Euríbor + term premium +
  // risk premium, constant over the projection — so it is above 7 % from the
  // first year or never.
  const bonoAlert = bono && scn.bono.some((v) => statusOf(v, bono.threshold, "gt") === "crossed")
    ? Math.max(...scn.bono) : null;
  const fromDefs = (ids: string[]) => ids
    .map((id) => defs.find((d) => d.id === id))
    .filter((d): d is RedLineDef => Boolean(d))
    .map((d) => ({
      label: d.label,
      why: WHY[d.id] ?? d.source,
      when: firstCrossing((scn as Record<string, number[]>)[d.series] ?? [], base[d.series] ?? [],
        d.threshold, d.cmp as "gt" | "lt"),
    }));
  const lines = fromDefs(DEBT_LINES);
  const others = fromDefs(OTHER_LINES);

  const snowK = scn.ief.findIndex((r, k) => r > scn.gnom[k]);
  const rows = [
    ...lines,
    {
      label: `Gasto público > ${nf(GTOT_RECORD.value, 1)} % PIB`,
      why: `Es el récord de España: ${GTOT_RECORD.year}, en plena pandemia.`,
      when: firstCrossing(scn.gtot, base.gtot, GTOT_RECORD.value, "gt"),
    },
    {
      label: `Intereses de la deuda > ${nf(INT_RECORD.value, 1)} % PIB`,
      why: `Es el récord de España: ${INT_RECORD.year}, cuando los tipos aún eran altos.`,
      when: firstCrossing(scn.int, base.int, INT_RECORD.value, "gt"),
    },
    {
      label: "Bola de nieve de la deuda",
      why: "El tipo medio que paga la deuda supera lo que crece la economía: la deuda crece sola aunque el Estado no gaste más de lo que ingresa.",
      when: (snowK < 0 ? { kind: "nunca" } : snowK > 0 ? { kind: "desde", year: YEARS[snowK] }
        : base.ief[0] > base.gnom[0] ? { kind: "hoy" } : { kind: "palancas" }) as When,
    },
  ];

  return (
    <div className="card">
      <h4>¿Cuándo es demasiada deuda? <small>las alarmas de tu escenario, año a año</small></h4>
      {bonoAlert !== null && (
        <p className="danger-note" role="alert">
          <span aria-hidden="true">⚠</span>{" "}
          Con tus palancas, el bono a 10 años se pagaría al {nf(bonoAlert, 2)} %, por
          encima de la línea roja del 7 %: la zona en la que Grecia, Portugal e
          Irlanda pidieron el rescate, y la que España tocó en 2012 con un 7,6 %.
          A ese precio, cada euro de deuda que se renueva sale mucho más caro y la
          bola de nieve se acelera.
        </p>
      )}
      <HowToRead>
        <p>
          Ningún modelo puede decir si una deuda se podrá pagar: depende de lo
          que acepten los mercados y de lo que decidan los gobiernos, y esta
          herramienta no lo decide. Lo que hace es encender alarmas cuando tu
          escenario pasa por niveles que ya trajeron problemas de verdad.
        </p>
        <p>
          Cada año del escenario se compara cada cifra con su umbral. La alarma
          salta el primer año en que lo pasa, y en el semáforo aparece como
          «cruzada»; «cerca» quiere decir que está a menos de un 10 % del umbral.
          Si ya está cruzada hoy, es que España ya está por encima, no que tus
          palancas la hayan roto.
        </p>
      </HowToRead>
      <table className="guide-t alarm-t" style={{ width: "100%" }}>
        <thead>
          <tr><th>Alarma</th><th>Con tus palancas</th><th>Por qué ese nivel</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.label}>
              <td>{r.label}</td>
              <td className={r.when.kind === "nunca" ? "ok" : "bad"}>{whenText(r.when)}</td>
              <td className="dim">{r.why}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {others.length > 0 && (
        <>
          <p style={{ fontWeight: 700, margin: "14px 0 4px" }}>Y las demás líneas rojas, fuera de la deuda</p>
          <table className="guide-t alarm-t" style={{ width: "100%" }}>
            <thead>
              <tr><th>Alarma</th><th>Con tus palancas</th><th>Por qué ese nivel</th></tr>
            </thead>
            <tbody>
              {others.map((r) => (
                <tr key={r.label}>
                  <td>{r.label}</td>
                  <td className={r.when.kind === "nunca" ? "ok" : "bad"}>{whenText(r.when)}</td>
                  <td className="dim">{r.why}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
      <p className="muted" style={{ fontSize: 13.5, margin: "8px 0 0" }}>
        El indicador de riesgo que sigue compara tu situación con la de los países
        que acabaron en impago. Es orientativo: no es una probabilidad de impago
        calibrada.
      </p>
    </div>
  );
}
