import { useState } from "react";
import { useExplain, usePrediction } from "../api/hooks";
import { useScenarioStore } from "../state/scenarioStore";
import { seriesOf } from "../engine/derived";
import type { Scenario } from "../engine/spain";
import { YEARS } from "../engine/spain";
import { nf } from "../lib/fmt";
import { ProjectionChart } from "./ProjectionChart";
import { SERIES_FORMAT } from "./KpiRow";
import type { PersonaQuestion } from "../personas/questions";

function fmt(key: string, v: number): string {
  const f = SERIES_FORMAT[key] ?? { dec: 1, unit: "" };
  return `${nf(v, f.dec)} ${f.unit}`.trim();
}

/** One evidence layer, collapsed until asked for.
 *
 *  Collapsed rather than absent: the reader who wants the number gets the
 *  number, and the reader who wants to argue with it can open the drawer.
 *  Putting all four open at once is the overwhelming page this replaces. */
function Layer({ title, tag, children }: {
  title: string; tag: string; children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className={open ? "layer open" : "layer"}>
      <button type="button" className="layer-head" onClick={() => setOpen((v) => !v)}>
        <span className="layer-tag">{tag}</span>
        <span className="layer-title">{title}</span>
        <span className="layer-caret">{open ? "▾" : "▸"}</span>
      </button>
      {open && <div className="layer-body">{children}</div>}
    </div>
  );
}

export function AnswerPanel({
  q, all, scn, base, k, year, onAsk, estimated,
}: {
  q: PersonaQuestion;
  all: PersonaQuestion[];
  scn: Scenario;
  base: Scenario;
  k: number;
  year: number;
  onAsk: (id: string) => void;
  estimated?: { name: string; value: number; ci_low: number; ci_high: number; calibrated_v16: number | null }[];
}) {
  const prediction = usePrediction();
  const levers = useScenarioStore((s) => s.levers);
  // Narrated over the series this question resolves to, so the prose is about
  // the number on screen. facts come from the engine; the model only writes.
  const explain = useExplain(levers, year, true, q.series);

  const value = seriesOf(scn, q.series)[k];
  const baseValue = seriesOf(base, q.series)[k];
  const delta = value - baseValue;

  return (
    <div className="answer">
      <div className="answer-headline">
        <span className="answer-q">{q.text}</span>
        <div className="answer-value">
          {fmt(q.series, value)}
          <small> en {year}</small>
        </div>
        {Math.abs(delta) > 1e-9 && (
          <p className="answer-delta">
            {delta > 0 ? "+" : ""}{fmt(q.series, delta)} frente al escenario base
            {" "}(que da {fmt(q.series, baseValue)}).
          </p>
        )}
      </div>

      <div className={q.companion ? "answer-charts two" : "answer-charts"}>
        <div className="card">
          <h4>{q.text} <small>base punteada vs escenario</small></h4>
          <ProjectionChart
            years={YEARS}
            baseline={seriesOf(base, q.series)}
            scenario={seriesOf(scn, q.series)}
            unit={SERIES_FORMAT[q.series]?.unit ?? ""}
            dec={SERIES_FORMAT[q.series]?.dec ?? 1}
          />
        </div>
        {q.companion && (
          <div className="card">
            <h4>Para leerlo bien <small>{q.companion}</small></h4>
            <ProjectionChart
              years={YEARS}
              baseline={seriesOf(base, q.companion)}
              scenario={seriesOf(scn, q.companion)}
              unit={SERIES_FORMAT[q.companion]?.unit ?? ""}
              dec={SERIES_FORMAT[q.companion]?.dec ?? 1}
            />
          </div>
        )}
      </div>

      <div className="layers">
        <Layer tag="motor" title="Cómo se calcula este número">
          {q.mechanism && <p>{q.mechanism}</p>}
          {explain.isSuccess && (
            <>
              <p>{explain.data.mecanismo}</p>
              {explain.data.contributions.length > 0 && (
                <>
                  <p className="layer-note">
                    De cuánto responde cada palanca en el movimiento de este año:
                  </p>
                  <ul className="layer-list">
                    {explain.data.contributions
                      .filter((ct) => Math.abs(ct.share) > 0.01)
                      .map((ct) => (
                        <li key={ct.lever_id}>
                          {ct.lever_name}: {nf(ct.delta, 2)}{" "}
                          <span className="muted">({nf(ct.share * 100, 0)} %)</span>
                        </li>
                      ))}
                  </ul>
                </>
              )}
              <p className="layer-note">
                {explain.data.source === "llm"
                  ? `Texto redactado por ${explain.data.model} sobre las cifras del motor; el modelo escribe, no calcula.`
                  : "Texto generado con plantillas deterministas sobre las cifras del motor."}
              </p>
            </>
          )}
          <p className="layer-note">
            Es un escenario condicionado a las palancas, no una predicción: el
            motor responde «si el tipo fuera X, esto saldría Y», no «esto va a pasar».
          </p>
        </Layer>

        {estimated && estimated.length > 0 && (
          <Layer tag="datos" title="Qué parámetros vienen de los datos">
            <ul className="layer-list">
              {estimated.map((e) => (
                <li key={e.name}>
                  <code>{e.name}</code> = {nf(e.value, 2)}{" "}
                  <span className="muted">[{nf(e.ci_low, 2)}, {nf(e.ci_high, 2)}]</span>
                  {e.calibrated_v16 !== null && (
                    <> — la calibración v16 usaba {nf(e.calibrated_v16, 2)}, fuera de esa banda.</>
                  )}
                </li>
              ))}
            </ul>
            <p className="layer-note">
              Estimado del panel de 20 CCAA. Los demás parámetros del motor
              (Okun, Phillips, multiplicador) siguen calibrados: el corte de datos
              congelado no permite identificarlos.
            </p>
          </Layer>
        )}

        <Layer tag="modelo" title="Qué dice el modelo de aprendizaje profundo">
          {prediction.isSuccess && prediction.data.available ? (
            <>
              <p>
                Un modelo global entrenado en {nf(Number(prediction.data.protocol.train_series), 0)} series
                de EE. UU. y Reino Unido, sin ver ningún dato español, y evaluado
                sobre las {prediction.data.protocol.n_ccaa} CCAA desde {prediction.data.protocol.test_start}.
              </p>
              <table className="layer-table">
                <thead>
                  <tr><th>horizonte</th><th>MASE modelo</th><th>MASE deriva</th><th /></tr>
                </thead>
                <tbody>
                  {prediction.data.rows.slice(0, 4).map((r) => {
                    const dl = r.mase.dl_global, dr = r.mase.drift;
                    return (
                      <tr key={r.h}>
                        <td>{r.h}T</td>
                        <td>{nf(dl, 3)}</td>
                        <td>{nf(dr, 3)}</td>
                        <td className={dl < dr ? "ok" : "bad"}>{dl < dr ? "gana" : "pierde"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {prediction.data.verdict && (
                <p className="layer-warn">
                  Veredicto: <strong>{prediction.data.verdict.verdict}</strong> — bate a
                  la deriva en {prediction.data.verdict.beaten_ccaa} de{" "}
                  {prediction.data.verdict.total_ccaa} CCAA, y harían falta{" "}
                  {prediction.data.verdict.required}. Por eso esta pantalla no
                  enseña una predicción puntual: el modelo no ha ganado el derecho
                  a hacerla, y la deriva es el listón que tendría que superar.
                </p>
              )}
            </>
          ) : (
            <p className="muted">Backtest no disponible en este despliegue.</p>
          )}
        </Layer>

        <Layer tag="límites" title="Qué no sabe este número">
          {explain.isSuccess && explain.data.advertencia && (
            <p>{explain.data.advertencia}</p>
          )}
          <ul className="layer-list">
            <li>
              Es un escenario condicional. Nadie, ni este motor ni un modelo de
              aprendizaje profundo, predice la macroeconomía a {year - 2026} años vista
              con precisión útil.
            </li>
            <li>
              El motor es semi-estructural: impone relaciones (Okun, Phillips, identidad
              de la deuda) en lugar de aprenderlas. Si esas relaciones cambian, el
              escenario no se entera.
            </li>
            <li>
              Sólo dos parámetros de vivienda están estimados; el resto son
              calibraciones heredadas que el corte de datos no puede contrastar.
            </li>
            <li>
              Vintage congelado: los datos de partida son de 2026-07-31 y no se actualizan.
            </li>
          </ul>
        </Layer>
      </div>

      <div className="followups">
        <span className="followups-lab">Seguir preguntando</span>
        {q.followUps.map((id) => {
          const next = all.find((x) => x.id === id);
          if (!next) return null;
          return (
            <button key={id} type="button" className="example-chip" onClick={() => onAsk(id)}>
              {next.text}
            </button>
          );
        })}
      </div>
    </div>
  );
}
