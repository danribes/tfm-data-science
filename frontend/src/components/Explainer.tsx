import { useState } from "react";
import { useExplain } from "../api/hooks";
import { useScenarioStore } from "../state/scenarioStore";
import { ContributionChart } from "./ContributionChart";

/** The persistent explanation panel.
 *
 *  Layered on purpose: `resumen` is plain Spanish and always visible, the
 *  mechanism with its coefficients sits behind a disclosure. One component
 *  serves both a general reader and a tribunal without writing the text twice.
 *
 *  The provenance line is not decoration. A reader is entitled to know whether
 *  a language model wrote the words or the deterministic templates did, and the
 *  numbers are the engine's either way. */
export function Explainer() {
  const levers = useScenarioStore((s) => s.levers);
  const horizon = useScenarioStore((s) => s.horizon);
  const [openMech, setOpenMech] = useState(false);
  const q = useExplain(levers, horizon);

  if (q.isError) {
    return (
      <aside className="explainer">
        <div className="explainer-h">Qué está pasando</div>
        <div className="banner err">
          No se pudo generar la explicación. Los gráficos siguen siendo válidos:
          se calculan en tu navegador con el motor local.
        </div>
      </aside>
    );
  }

  if (!q.data) {
    return (
      <aside className="explainer">
        <div className="explainer-h">Qué está pasando</div>
        <p className="explainer-loading">Leyendo el escenario…</p>
      </aside>
    );
  }

  const d = q.data;
  const isLlm = d.source === "llm";

  return (
    <aside className="explainer" aria-live="polite">
      <div className="explainer-h">
        Qué está pasando
        {q.isFetching && <span className="explainer-busy" aria-label="actualizando" />}
      </div>

      <p className="explainer-resumen">{d.resumen}</p>

      <ContributionChart
        contributions={d.contributions}
        interaction={d.interaction}
        jointDelta={d.joint_delta}
        year={d.headline_year}
      />

      {d.mecanismo && (
        <div className="explainer-mech">
          <button
            type="button"
            className="mech-toggle"
            aria-expanded={openMech}
            onClick={() => setOpenMech((v) => !v)}
          >
            {openMech ? "▾" : "▸"} ver el mecanismo
          </button>
          {openMech && <pre className="mech-body">{d.mecanismo}</pre>}
        </div>
      )}

      <p className="explainer-warn">{d.advertencia}</p>

      <p className="explainer-prov">
        {isLlm ? (
          <>
            Texto redactado por <code>{d.model}</code> a partir de cifras
            calculadas por el motor. El modelo elige las palabras, nunca los
            números.
          </>
        ) : (
          <>
            Texto generado con plantillas deterministas sobre las cifras del
            motor{d.fallback_reason ? " (sin narración por IA en esta sesión)" : ""}.
          </>
        )}
      </p>
    </aside>
  );
}
