import { useState } from "react";
import { useMonteCarlo, useRedlines } from "../api/hooks";
import { baseline, YEARS } from "../engine/spain";
import { ALL_SERIES_KEYS, seriesOf, type AnySeriesKey } from "../engine/derived";
import { LEVER_SPECS } from "../engine/levers";
import { BASE_LEVERS } from "../engine/vintage";
import { nf } from "../lib/fmt";
import { FanChart } from "../components/FanChart";
import { ProjectionChart } from "../components/ProjectionChart";
import { SERIES_FORMAT } from "../components/KpiRow";
import { useScenario, useScenarioStore } from "../state/scenarioStore";

export default function Laboratorio() {
  const [seriesKey, setSeriesKey] = useState<AnySeriesKey>("b");
  const scn = useScenario();
  const levers = useScenarioStore((s) => s.levers);
  const redlines = useRedlines();
  const mc = useMonteCarlo(levers, true);
  const base = baseline();
  const f = SERIES_FORMAT[seriesKey] ?? { dec: 1, unit: "" };
  const bound = (redlines.data?.redlines ?? [])
    .filter((rl) => rl.series === seriesKey)
    .map((rl) => ({ value: rl.threshold, label: rl.label }));

  return (
    <div>
      <div className="head"><h1>Laboratorio</h1>
        <span className="meta">explorador de las 40 series del motor + abanico Monte Carlo (servidor)</span>
      </div>

      <div className="card">
        <h4>
          <label htmlFor="serie-select">Serie</label>
          <small>{seriesKey} · {f.unit || "índice"}</small>
        </h4>
        <select id="serie-select" aria-label="Serie" value={seriesKey}
          onChange={(e) => setSeriesKey(e.target.value as AnySeriesKey)}
          style={{ maxWidth: 320, marginBottom: 8 }}>
          {ALL_SERIES_KEYS.map((k) => <option key={k} value={k}>{k}</option>)}
        </select>
        <ProjectionChart years={YEARS} baseline={seriesOf(base, seriesKey)}
          scenario={seriesOf(scn, seriesKey)} redLines={bound} unit={f.unit} dec={f.dec} />
      </div>

      <div className="row2">
        <div className="card">
          <h4>Abanico Monte Carlo · deuda/PIB hasta 2070
            <small>{mc.data ? `${mc.data.n_paths} trayectorias · semilla ${mc.data.seed}` : "4000 trayectorias · semilla 42"}</small>
          </h4>
          {mc.isError && <div className="banner err">Monte Carlo no disponible — el resto de la app sigue funcionando.</div>}
          {mc.isPending && !mc.data && <p style={{ fontSize: 12 }}>Calculando abanico…</p>}
          {mc.data && <FanChart years={mc.data.years} percentiles={mc.data.percentiles} />}
          <p className="src" style={{ whiteSpace: "normal" }}>
            El abanico se calcula en el servidor (Python). Validación: envolvente dorada
            gold_escenarios_deuda_mc.csv con tolerancia ±2 pp en 2030/2050/2070 — los pines de
            semilla 42 del fixture atan solo al motor Python.
          </p>
        </div>
        <div className="card">
          <h4>Palancas en crudo <small>vector actual vs base congelada</small></h4>
          <table style={{ fontSize: 11, borderCollapse: "collapse", width: "100%" }}>
            <thead>
              <tr><th style={{ textAlign: "left" }}>palanca</th><th>actual</th><th>base</th></tr>
            </thead>
            <tbody>
              {LEVER_SPECS.map((s) => (
                <tr key={s.id}>
                  <td>{s.sym} · {s.nm}</td>
                  <td style={{ textAlign: "right" }}>{nf(levers[s.id], s.dec)}</td>
                  <td style={{ textAlign: "right", color: "var(--muted)" }}>{nf(BASE_LEVERS[s.id], s.dec)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
