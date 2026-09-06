import { useState } from "react";
import { useMonteCarlo, useRedlines, useSensitivity } from "../api/hooks";
import { API_BASE } from "../api/client";
import { baseline, YEARS } from "../engine/spain";
import { ALL_SERIES_KEYS, seriesOf, type AnySeriesKey } from "../engine/derived";
import { LEVER_SPECS } from "../engine/levers";
import { BASE_LEVERS } from "../engine/vintage";
import { nf, sg } from "../lib/fmt";
import { Caption } from "../components/Caption";
import { FanChart } from "../components/FanChart";
import { ProjectionChart } from "../components/ProjectionChart";
import { SERIES_FORMAT } from "../components/KpiRow";
import { useScenario, useScenarioStore } from "../state/scenarioStore";

import { BudgetFlowChart } from "../components/BudgetFlowChart";
import { DebtAmortizationFlowChart } from "../components/DebtAmortizationFlowChart";
import { EmpiricalTwin } from "../components/EmpiricalTwin";
import { AnalogPanel } from "../components/AnalogPanel";

export default function Laboratorio() {
  const [seriesKey, setSeriesKey] = useState<AnySeriesKey>("b");
  const scn = useScenario();
  const levers = useScenarioStore((s) => s.levers);
  const horizon = useScenarioStore((s) => s.horizon);
  const redlines = useRedlines();
  const mc = useMonteCarlo(levers, true);
  const sens = useSensitivity(levers);
  const base = baseline();
  const f = SERIES_FORMAT[seriesKey] ?? { dec: 1, unit: "" };
  const bound = (redlines.data?.redlines ?? [])
    .filter((rl) => rl.series === seriesKey)
    .map((rl) => ({ value: rl.threshold, label: rl.label }));

  return (
    <div>
      <div className="head" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1>Laboratorio</h1>
          <span className="meta">explorador de las 40 series del motor + abanico Monte Carlo + matriz de sensibilidad + flujo presupuestario</span>
        </div>
        <a
          href={`${API_BASE}/scenario/report`}
          target="_blank"
          rel="noreferrer"
          style={{
            padding: "10px 16px",
            background: "var(--accent, #0284c7)",
            color: "#ffffff",
            borderRadius: 6,
            textDecoration: "none",
            fontSize: 14,
            fontWeight: 600,
            whiteSpace: "nowrap",
          }}
        >
          📄 Informe de política pública · versión imprimible
        </a>
      </div>

      <div className="card">
        <h4>
          <label htmlFor="serie-select">Serie</label>
          <small>{seriesKey} · {f.unit || "índice"}</small>
        </h4>
        <select id="serie-select" aria-label="Serie" value={seriesKey}
          onChange={(e) => setSeriesKey(e.target.value as AnySeriesKey)}
          style={{ maxWidth: 320, marginBottom: 8, fontSize: 14 }}>
          {ALL_SERIES_KEYS.map((k) => <option key={k} value={k}>{k}</option>)}
        </select>
        <ProjectionChart years={YEARS} baseline={seriesOf(base, seriesKey)}
          scenario={seriesOf(scn, seriesKey)} redLines={bound} unit={f.unit} dec={f.dec} />
        <Caption>
          La línea continua es tu escenario; la punteada es la base congelada del
          vintage. La distancia entre ambas es lo único que has causado tú — todo
          lo demás ya estaba en los datos.
        </Caption>
      </div>

      <div className="row2" style={{ marginBottom: 16 }}>
        <div className="card">
          <h4>Abanico Monte Carlo · deuda/PIB hasta 2070
            <small>{mc.data ? `${nf(mc.data.n_paths, 0)} trayectorias · semilla ${mc.data.seed}` : `${nf(4000, 0)} trayectorias · semilla 42`}</small>
          </h4>
          {mc.isError && <div className="banner err">Monte Carlo no disponible — el resto de la app sigue funcionando.</div>}
          {mc.isPending && !mc.data && <p style={{ fontSize: 14 }}>Calculando abanico…</p>}
          {mc.data && <FanChart years={mc.data.years} percentiles={mc.data.percentiles} />}
          <Caption>
            Lo que informa aquí es la anchura de la banda, no la mediana. Si las
            bandas se abren en abanico, el resultado central importa poco.
          </Caption>
          <p className="src" style={{ whiteSpace: "normal" }}>
            El abanico se calcula en el servidor (Python). Validación: envolvente dorada
            gold_escenarios_deuda_mc.csv con tolerancia ±2 pp en 2030/2050/2070 — los pines de
            semilla 42 del fixture atan solo al motor Python.
          </p>
        </div>
        <div className="card">
          <h4>Palancas en crudo <small>vector actual vs base congelada</small></h4>
          <table style={{ fontSize: 13.5, borderCollapse: "collapse", width: "100%" }}>
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

      {/* --- Budget & Debt Flow Sankey Diagrams --- */}
      <BudgetFlowChart levers={levers} />
      <DebtAmortizationFlowChart levers={levers} />

      <EmpiricalTwin />

      <AnalogPanel levers={levers} horizon={horizon} />

      <div className="card" style={{ marginTop: 16 }}>
        <h4>Matriz de Sensibilidad y Elasticidades Marginales <small>∂Y / ∂L en 2030 y 2050</small></h4>
        {sens.isPending && <p style={{ fontSize: 14 }}>Calculando derivadas numéricas del escenario…</p>}
        {sens.data && (
          <table style={{ fontSize: 13.5, borderCollapse: "collapse", width: "100%" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left" }}>Palanca (L_k)</th>
                <th style={{ textAlign: "right" }}>Deuda 2050 · de tope a tope</th>
                <th style={{ textAlign: "right" }}>Deuda 2030 · de tope a tope</th>
                <th style={{ textAlign: "right" }}>∂(Deuda)/∂L (2050)</th>
                <th style={{ textAlign: "right" }}>∂(Paro)/∂L (2030)</th>
                <th style={{ textAlign: "right" }}>∂(IPCA)/∂L (2030)</th>
                <th style={{ textAlign: "right" }}>∂(Vivienda)/∂L (2030)</th>
              </tr>
            </thead>
            <tbody>
              {/* Ordered by the comparable column, never by the raw derivative:
                  ranking rows in mixed units is the misreading this table has
                  to avoid, not one it should present sorted. */}
              {[...LEVER_SPECS]
                .sort((a, b) => Math.abs(sens.data?.matrix[b.id]?.span_effects["2050"]?.b ?? 0)
                              - Math.abs(sens.data?.matrix[a.id]?.span_effects["2050"]?.b ?? 0))
                .map((spec) => {
                const row = sens.data?.matrix[spec.id];
                const s30 = row?.sensitivities["2030"] ?? {};
                const s50 = row?.sensitivities["2050"] ?? {};
                const e30 = row?.span_effects["2030"] ?? {};
                const e50 = row?.span_effects["2050"] ?? {};
                return (
                  <tr key={spec.id}>
                    <td><strong>{spec.sym}</strong> · {spec.nm} ({spec.unit})</td>
                    <td style={{ textAlign: "right", fontWeight: 700 }}>{sg(e50["b"] ?? 0, 1)}</td>
                    <td style={{ textAlign: "right", fontWeight: 700 }}>{sg(e30["b"] ?? 0, 1)}</td>
                    <td style={{ textAlign: "right" }} className="dim">{sg(s50["b"] ?? 0, 2)}</td>
                    <td style={{ textAlign: "right" }} className="dim">{sg(s30["u"] ?? 0, 2)}</td>
                    <td style={{ textAlign: "right" }} className="dim">{sg(s30["pi"] ?? 0, 2)}</td>
                    <td style={{ textAlign: "right" }} className="dim">{sg(s30["esf"] ?? 0, 2)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
        <Caption>
          Las dos primeras columnas son <b>puntos de PIB de deuda</b> si esa palanca se
          mueve de un extremo a otro de su recorrido. Esa es la única columna que se
          puede leer hacia abajo: hace la misma pregunta a todas las palancas.
        </Caption>
        <Caption>
          Las columnas ∂Y/∂L en gris son la derivada por <i>una unidad</i> de cada
          palanca, y las unidades no son la misma cosa — <code>r</code> va en puntos
          porcentuales, <code>σ</code> en puntos básicos, <code>β</code> es un
          multiplicador. Comparar filas ahí engaña: la presión demográfica marca
          {" "}{sg(sens.data?.matrix["dem"]?.sensitivities["2050"]?.b ?? 0, 2)} frente a
          {" "}{sg(sens.data?.matrix["r"]?.sensitivities["2050"]?.b ?? 0, 2)} del tipo de
          interés, y sin embargo, movidas de tope a tope, el tipo pesa más.
        </Caption>
      </div>
    </div>
  );
}
