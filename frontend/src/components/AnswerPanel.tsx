import { useState } from "react";
import { useExplain, usePrediction, useRagSearch } from "../api/hooks";
import { useScenarioStore } from "../state/scenarioStore";
import { seriesOf } from "../engine/derived";
import type { Scenario } from "../engine/spain";
import { YEARS } from "../engine/spain";
import { eur, nf } from "../lib/fmt";
import { ProjectionChart } from "./ProjectionChart";
import { SERIES_FORMAT } from "./KpiRow";
import { RagCorpusNotice } from "./RagCorpusNotice";
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

/** Source passages load only when the reader opens the drawer. */
function CorpusLayer({ concept }: { concept: string }) {
  const [open, setOpen] = useState(false);
  const corpus = useRagSearch(concept, open);
  const error = corpus.error as { detail?: string; message?: string } | null;
  const passages = corpus.data?.passages ?? [];

  return (
    <div className={open ? "layer open" : "layer"}>
      <button type="button" className="layer-head" onClick={() => setOpen((v) => !v)}>
        <span className="layer-tag">fuentes</span>
        <span className="layer-title">Fuentes sobre «{concept}»</span>
        <span className="layer-caret">{open ? "▾" : "▸"}</span>
      </button>
      {open && (
        <div className="layer-body">
          <RagCorpusNotice data={corpus.corpus} />
          {corpus.isPending && <p className="muted">Buscando en el corpus…</p>}
          {corpus.isError && (
            <p className="layer-note">
              No se ha podido consultar el corpus: {error?.detail ?? error?.message ?? "error desconocido"}.
            </p>
          )}
          {corpus.emptyCollection && <p className="layer-note">No hay colecciones con pasajes disponibles.</p>}
          {corpus.isSuccess && passages.length === 0 && (
            <p className="layer-note">
              El corpus no cubre este concepto. Prefiero decirlo a devolver un
              pasaje que no viene a cuento.
            </p>
          )}
          {corpus.isSuccess && passages.length > 0 && (
            <>
              <ol className="layer-list">
                {passages.map((p, i) => (
                  <li key={i}>
                    <span className="psg-cite">{p.cita}</span>
                    <span className={`psg-auth ${p.authority}`}>{p.authority}</span>
                    <p className="psg-text">{p.text.slice(0, 320)}…</p>
                  </li>
                ))}
              </ol>
              <p className="layer-note">
                Pasajes recuperados del corpus, no generados. Contexto sobre el
                concepto: no son la fuente de la cifra, que sale del motor.
              </p>
            </>
          )}
        </div>
      )}
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
  /** Los dos parámetros que el motor sí estima, con la muestra de la que
   *  salen. `label` y `source` vienen de la API: escribirlos a mano aquí es
   *  como la ficha acabó afirmando «panel de 20 CCAA» cuando son 19. */
  estimated?: {
    name: string; label?: string; value: number; ci_low: number; ci_high: number;
    n?: number; n_units?: number; source?: string;
  }[];
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
          <h4>{q.text} <small>línea de partida punteada · escenario en continuo</small></h4>
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
          <Layer tag="datos" title="En qué se apoya esta cifra">
            <ul className="layer-list">
              {estimated.map((e) => (
                <li key={e.name}>
                  {e.label ?? e.name}: <b>{nf(e.value, 2)}</b>{" "}
                  <span className="muted">
                    (banda al 90 % [{nf(e.ci_low, 2)}, {nf(e.ci_high, 2)}])
                  </span>
                  {e.source && <div className="muted">{e.source}</div>}
                  {e.n !== undefined && e.n_units !== undefined && (
                    <div className="muted">
                      {eur(e.n)} observaciones trimestrales de {e.n_units} comunidades
                    </div>
                  )}
                </li>
              ))}
            </ul>
            <p className="layer-note">
              Son los dos únicos parámetros del motor estimados sobre datos, y
              los dos actúan sobre la vivienda. La banda es la incertidumbre de
              esa estimación: por eso el precio de la vivienda es la única serie
              del panel que se publica con banda.
            </p>
            <p className="layer-note">
              El resto de constantes —Okun, Phillips, el multiplicador fiscal—
              están <b>calibradas</b>: valores tomados de la literatura, no
              medidos sobre este corte de datos, que no permite identificarlos.
              Son supuestos, y un revisor puede discutirlos.
            </p>
          </Layer>
        )}

        {q.concept && <CorpusLayer concept={q.concept} />}

        <Layer tag="modelo" title="Qué dice el modelo de aprendizaje profundo">
          {prediction.isSuccess && prediction.data.available ? (
            <>
              <p>
                Un modelo global entrenado en {nf(Number(prediction.data.protocol.train_series), 0)} series
                de EE. UU. y Reino Unido, sin ver ningún dato español, y evaluado
                sobre las {prediction.data.protocol.n_ccaa} CCAA desde {prediction.data.protocol.test_start}.
              </p>
              <p className="layer-note">
                Se compara con la regla más tonta posible: prolongar la línea
                recta de los últimos años, lo que en la jerga se llama deriva
                («drift»). La medida es el error escalado medio (MASE); cuanto
                más bajo, mejor.
              </p>
              <table className="layer-table">
                <thead>
                  <tr>
                    <th>horizonte</th><th>error del modelo</th>
                    <th>error de la deriva</th><th />
                  </tr>
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

      {explain.isSuccess && explain.data.coloquial && (
        <div className="coloquial">
          <span className="coloquial-lab">Y en corto</span>
          <p>{explain.data.coloquial}</p>
        </div>
      )}

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
