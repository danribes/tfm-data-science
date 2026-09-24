import { useState } from "react";
import { useMonteCarlo, useRedlines, useSensitivity } from "../api/hooks";
import { API_BASE } from "../api/client";
import { baseline, YEARS } from "../engine/spain";
import { ALL_SERIES_KEYS, seriesOf, type AnySeriesKey } from "../engine/derived";
import { LEVER_SPECS } from "../engine/levers";
import { BASE_LEVERS } from "../engine/vintage";
import { eur, nf, sg } from "../lib/fmt";
import { Caption } from "../components/Caption";
import { FanChart } from "../components/FanChart";
import { ProjectionChart } from "../components/ProjectionChart";
import { SERIES_FORMAT } from "../components/KpiRow";
import { useScenario, useScenarioStore } from "../state/scenarioStore";

import { BudgetFlowChart } from "../components/BudgetFlowChart";
import { DebtAmortizationFlowChart } from "../components/DebtAmortizationFlowChart";
import { EmpiricalTwin } from "../components/EmpiricalTwin";
import { AnalogPanel } from "../components/AnalogPanel";
import { HowToRead, TechDetails } from "../components/HowToRead";
import { anioDeConsulta } from "../lib/analogHorizon";
import { seriesLabel, seriesPlain } from "../lib/seriesMeta";

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
          <span className="meta">el modelo por dentro: cada cifra, su incertidumbre, el dinero público y qué supuesto pesa más</span>
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

      <HowToRead>
        <p>
          Aquí se mira el modelo por dentro. Tres palabras salen en toda la página:
        </p>
        <p>
          <b>Palanca</b>: un supuesto que eliges tú en el panel de palancas, como
          el tipo de interés o cuánto suben las pensiones. El modelo calcula qué
          pasaría con todo lo demás si ese supuesto se cumpliera.
        </p>
        <p>
          <b>Base</b>: lo que sale sin tocar ninguna palanca, con los datos de
          partida de julio de 2026.
        </p>
        <p>
          <b>% del PIB</b>: una cifra comparada con todo lo que produce España en
          un año. Una deuda del 100 % del PIB equivale a un año entero de producción.
        </p>
      </HowToRead>

      <div className="card">
        <h4>
          <label htmlFor="serie-select">Explora una cifra</label>
          <small>{seriesLabel(seriesKey)} · {f.unit || "índice"}</small>
        </h4>
        <HowToRead>
          <p>
            Elige una cifra en el desplegable. La línea continua es lo que sale con
            tus supuestos; la punteada, lo que saldría sin tocar nada. Si van
            juntas, tus cambios apenas afectan a esta cifra. Si aparece una línea
            roja, es un umbral de alerta, como una deuda por encima del 120 % del PIB.
          </p>
        </HowToRead>
        <select id="serie-select" aria-label="Serie" value={seriesKey}
          onChange={(e) => setSeriesKey(e.target.value as AnySeriesKey)}
          style={{ maxWidth: 320, marginBottom: 8, fontSize: 14 }}>
          {ALL_SERIES_KEYS.map((k) => <option key={k} value={k}>{seriesLabel(k)}</option>)}
        </select>
        {seriesPlain(seriesKey) && (
          <p className="muted" style={{ fontSize: 14, margin: "0 0 8px" }}>{seriesPlain(seriesKey)}</p>
        )}
        <ProjectionChart years={YEARS} baseline={seriesOf(base, seriesKey)}
          scenario={seriesOf(scn, seriesKey)} redLines={bound} unit={f.unit} dec={f.dec} />
        <Caption>
          Es lo que implica el modelo con tus supuestos, no una medida de lo que
          esos cambios causarían en la economía real.
        </Caption>
      </div>

      <div className="row2" style={{ marginBottom: 16 }}>
        <div className="card">
          <h4>¿Cuánta incertidumbre hay en la deuda? · hasta 2070
            <small>{eur(mc.data?.n_paths ?? 4000)} trayectorias simuladas</small>
          </h4>
          <HowToRead>
            <p>
              Nadie sabe qué tipos de interés, qué crecimiento o qué déficit habrá
              cada año. Por eso simulamos {eur(mc.data?.n_paths ?? 4000)} futuros
              posibles: en cada uno, esas tres cosas reciben sorpresas al azar que
              duran varios años, como pasa en la realidad.
            </p>
            <p>
              La línea es el futuro del medio: la mitad acaba por encima y la mitad
              por debajo. La banda interior recoge la mitad de los futuros; la
              exterior, más ancha, 9 de cada 10. Cuanto más se abre el abanico con
              los años, menos se sabe.
              No es una probabilidad garantizada: sólo refleja las sorpresas que
              hemos simulado.
            </p>
          </HowToRead>
          {mc.isError && <div className="banner err">Monte Carlo no disponible — el resto de la app sigue funcionando.</div>}
          {mc.isPending && !mc.data && <p style={{ fontSize: 14 }}>Calculando abanico…</p>}
          {mc.data && <FanChart years={mc.data.years} percentiles={mc.data.percentiles}
            outerLabel="9 de cada 10 futuros" innerLabel="la mitad de los futuros"
            centerLabel="el futuro del medio" />}
          {mc.data && [...Object.values(mc.data.percentiles), ...(mc.data.paths ?? [])]
            .some((series) => series.some((value) => value < 0)) && (
              <div className="banner" role="status">
                Algunas trayectorias o bandas mostradas alcanzan deuda negativa,
                fuera del dominio de deuda bruta. El modelo no representa la
                acumulación de activos ni la respuesta de política al agotar la deuda.
              </div>
            )}
          <TechDetails>
            <Caption>
              Choques AR(1) normales sobre r, g y sp; semilla {mc.data?.seed ?? 42}.
              La banda p5–p95 contiene el 90 % central de las trayectorias simuladas,
              condicionado a los choques y reglas elegidos. No se ha validado una
              cobertura predictiva del 90 % sobre datos reales.
            </Caption>
            <p className="src" style={{ whiteSpace: "normal" }}>
              El abanico se calcula en el servidor (Python). Comprobación de reproducción: envolvente dorada
              gold_escenarios_deuda_mc.csv con tolerancia ±2 pp en 2030/2050/2070 — los pines de
              semilla 42 del fixture atan solo al motor Python. Reproducir otra simulación
              no demuestra precisión predictiva; la incertidumbre paramétrica no está incluida.
            </p>
          </TechDetails>
        </div>
        <div className="card">
          <h4>Tus supuestos (palancas) <small>tu valor frente al de partida</small></h4>
          <HowToRead>
            <p>
              Cada palanca es un supuesto que cambias en el panel de palancas. Debajo
              de su nombre está lo que significa. En negrita, las que has movido.
            </p>
          </HowToRead>
          <table style={{ fontSize: 15, borderCollapse: "collapse", width: "100%" }}>
            <thead>
              <tr><th style={{ textAlign: "left" }}>palanca</th><th>tu valor</th><th>de partida</th></tr>
            </thead>
            <tbody>
              {LEVER_SPECS.map((s) => {
                const moved = levers[s.id] !== BASE_LEVERS[s.id];
                return (
                  <tr key={s.id} style={moved ? { fontWeight: 700 } : undefined}>
                    <td style={{ padding: "4px 0" }}>
                      {s.nm} <span className="dim">({s.unit})</span>
                      <div className="muted" style={{ fontSize: 13, fontWeight: 400, lineHeight: 1.4 }}>{s.plain}</div>
                    </td>
                    <td style={{ textAlign: "right", verticalAlign: "top" }}>{nf(levers[s.id], s.dec)}</td>
                    <td style={{ textAlign: "right", verticalAlign: "top", color: "var(--muted)" }}>{nf(BASE_LEVERS[s.id], s.dec)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* --- Budget & Debt Flow Sankey Diagrams --- */}
      <BudgetFlowChart levers={levers} horizon={horizon} />
      <DebtAmortizationFlowChart levers={levers} horizon={horizon} />

      <EmpiricalTwin />

      {/* Mismo suelo que en la portada: pedir el año de entrada devolvía
          un recorrido de un año y la trayectoria salía con un solo punto. */}
      <AnalogPanel levers={levers} horizon={anioDeConsulta(horizon)} />

      <div className="card" style={{ marginTop: 16 }}>
        <h4>¿Qué supuesto pesa más? <small>efecto de cada palanca en 2030 y 2050</small></h4>
        <HowToRead>
          <p>
            Para cada palanca, cuánto cambiaría la deuda, aproximadamente, si la
            llevaras de su valor más bajo al más alto. Se mide en puntos de PIB. Es
            la forma justa de compararlas, porque a todas se les hace la misma
            pregunta: las de arriba son las que más pesan.
          </p>
          <p>
            Un signo + quiere decir que subir esa palanca sube la deuda; un −, que la
            baja. Un 0 quiere decir que esa palanca no llega a la deuda en el modelo.
            Las columnas en gris son para especialistas: cuánto cambia cada cifra
            por una sola unidad de la palanca. Como cada palanca se mide en unidades
            distintas, no sirven para comparar unas filas con otras.
          </p>
        </HowToRead>
        {sens.isPending && <p style={{ fontSize: 14 }}>Calculando el efecto de cada palanca…</p>}
        {sens.data && (
          <table style={{ fontSize: 15, borderCollapse: "collapse", width: "100%" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left" }}>Palanca</th>
                <th style={{ textAlign: "right" }}>Deuda en 2050, del mínimo al máximo</th>
                <th style={{ textAlign: "right" }}>Deuda en 2030, del mínimo al máximo</th>
                <th style={{ textAlign: "right" }}>Por unidad: deuda 2050</th>
                <th style={{ textAlign: "right" }}>Por unidad: paro 2030</th>
                <th style={{ textAlign: "right" }}>Por unidad: inflación 2030</th>
                <th style={{ textAlign: "right" }}>Por unidad: esfuerzo vivienda 2030</th>
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
        <TechDetails>
          <Caption>
            Las dos primeras columnas son <b>puntos de PIB de deuda</b> si esa palanca
            se mueve de un extremo a otro de su recorrido: la derivada numérica en el
            escenario actual multiplicada por el recorrido del deslizador, una
            aproximación lineal. Es la única columna que se puede leer hacia abajo:
            hace la misma pregunta a todas las palancas.
          </Caption>
          <Caption>
            Las columnas en gris son la derivada ∂Y/∂L por <i>una unidad</i> de cada
            palanca, y las unidades no son la misma cosa — <code>r</code> va en puntos
            porcentuales, <code>σ</code> en puntos básicos, <code>β</code> es un
            multiplicador. Comparar filas ahí engaña: la presión demográfica marca
            {" "}{sg(sens.data?.matrix["dem"]?.sensitivities["2050"]?.b ?? 0, 2)} frente a
            {" "}{sg(sens.data?.matrix["r"]?.sensitivities["2050"]?.b ?? 0, 2)} del tipo de
            interés, y sin embargo, movidas de tope a tope, el tipo pesa más.
          </Caption>
        </TechDetails>
      </div>
    </div>
  );
}
