import { useState } from "react";
import { useExplain, usePrediction, useRagSearch } from "../api/hooks";
import { useScenarioStore } from "../state/scenarioStore";
import { seriesOf } from "../engine/derived";
import type { Scenario } from "../engine/spain";
import { YEARS } from "../engine/spain";
import { eur, nf, sgUnit } from "../lib/fmt";
import { ProjectionChart } from "./ProjectionChart";
import { SERIES_FORMAT } from "./KpiRow";
import { RagCorpusNotice } from "./RagCorpusNotice";
import { seriesLabel, seriesPlain } from "../lib/seriesMeta";
import type { PersonaQuestion } from "../personas/questions";

/** The only series the deep-learning backtest was run on. The layer shows
 *  under every question, but under any other one it says first that this
 *  number was never tested, so the house-price table does not read as if the
 *  network had been tried on paro or deuda. */
const HOUSE_PRICE_SERIES = new Set(["precio", "ipv"]);

/** The panel speaks in years, not quarter codes, and both ends of the scored
 *  window come from the API. The first origin is "2019Q4", so the first
 *  forecast lands in the quarter after it; the held-out tail starts at
 *  "2024Q1", so the last scored quarter is the one before it. */
function yearAfter(p: string): number {
  const [y, q] = p.split("Q").map(Number);
  return q === 4 ? y + 1 : y;
}
function yearBefore(p: string): number {
  const [y, q] = p.split("Q").map(Number);
  return q === 1 ? y - 1 : y;
}

/** A horizon in quarters, said the way a person says it. */
const plazo = (h: number) =>
  h % 4 === 0 ? (h === 4 ? "1 año" : `${h / 4} años`) : `${h * 3} meses`;

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
        {/* The question says what the reader asked, not what is measured:
            «¿Voy a encontrar trabajo?» over 21,5 % read as the overall
            unemployment rate when it is the under-25 one. */}
        <span className="answer-series">{seriesLabel(q.series)}</span>
        <div className="answer-value">
          {fmt(q.series, value)}
          <small> en {year}</small>
        </div>
        {seriesPlain(q.series) && <p className="answer-delta muted">{seriesPlain(q.series)}</p>}
        {Math.abs(delta) > 1e-9 && (
          <p className="answer-delta">
            {sgUnit(delta, SERIES_FORMAT[q.series]?.dec ?? 1, SERIES_FORMAT[q.series]?.unit ?? "")} frente al escenario base
            {" "}(que da {fmt(q.series, baseValue)}).
          </p>
        )}
      </div>

      <div className={q.companion ? "answer-charts two" : "answer-charts"}>
        <div className="card">
          <h4>{seriesLabel(q.series)} <small>línea de partida punteada · escenario en continuo</small></h4>
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
            <h4>Para leerlo bien <small>{seriesLabel(q.companion)}</small></h4>
            {seriesPlain(q.companion) && (
              <p className="muted" style={{ fontSize: 13.5, margin: "0 0 6px" }}>{seriesPlain(q.companion)}</p>
            )}
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
                          {ct.lever_name}: {sgUnit(ct.delta, SERIES_FORMAT[q.series]?.dec ?? 2, SERIES_FORMAT[q.series]?.unit ?? "")}{" "}
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

        <Layer tag="IA" title="¿Lo predeciría mejor una inteligencia artificial?">
          {prediction.isSuccess && prediction.data.available ? (
            <>
              {!HOUSE_PRICE_SERIES.has(q.series) && (
                <p className="layer-warn">
                  Con «{seriesLabel(q.series)}» no la hemos probado: para esta
                  cifra no hay ninguna predicción de inteligencia artificial.
                  Sí la probamos con el precio de la vivienda, y esto es lo que
                  salió.
                </p>
              )}
              <p>
                Lo probamos con el precio de la vivienda. Entrenamos una red
                neuronal —un tipo de inteligencia artificial, lo que se llama
                aprendizaje profundo— con los precios de{" "}
                {nf(Number(prediction.data.protocol.train_series), 0)} zonas de
                Estados Unidos y Reino Unido, sin enseñarle ni un solo dato de
                España. Después le pedimos que predijera los precios de las{" "}
                {prediction.data.protocol.n_ccaa} comunidades autónomas entre{" "}
                {yearAfter(String(prediction.data.protocol.origins).split("–")[0])} y{" "}
                {yearBefore(String(prediction.data.protocol.test_start))}, viendo en
                cada momento sólo lo que había pasado hasta entonces.
              </p>
              <p className="layer-note">
                Para saber si acierta, la comparamos con una regla muy sencilla:
                suponer que el precio seguirá subiendo (o bajando) al mismo ritmo
                que en los dos últimos años. En estadística se llama «deriva».
                Parece fácil de batir, pero la vivienda tiene mucha inercia y esta
                regla suele acertar bastante.
              </p>
              <p className="layer-note">
                Cuánto se equivoca cada una, de media, según lo lejos que mire
                (cuanto más bajo, mejor):
              </p>
              <table className="layer-table">
                <thead>
                  <tr>
                    <th>a</th><th>fallo de la IA</th>
                    <th>fallo de la regla</th><th>acierta más</th>
                  </tr>
                </thead>
                <tbody>
                  {prediction.data.rows.filter((r) => r.h <= (prediction.data.verdict?.horizon ?? 4)).map((r) => {
                    const dl = r.mase.dl_global, dr = r.mase.drift;
                    return (
                      <tr key={r.h}>
                        <td>{plazo(r.h)}</td>
                        <td>{nf(dl, 3)}</td>
                        <td>{nf(dr, 3)}</td>
                        <td className={dl < dr ? "ok" : "bad"}>{dl < dr ? "la IA" : "la regla"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {prediction.data.verdict && (
                <p className="layer-warn">
                  {prediction.data.verdict.wins ? (
                    <>
                      <strong>Resultado: gana la inteligencia artificial.</strong>{" "}
                      Comunidad por comunidad, acierta más que la regla en{" "}
                      {prediction.data.verdict.beaten_ccaa} de las{" "}
                      {prediction.data.verdict.total_ccaa}; antes de empezar pusimos
                      el listón en {prediction.data.verdict.required}.
                    </>
                  ) : (
                    <>
                      <strong>Resultado: gana la regla sencilla.</strong>{" "}
                      Comunidad por comunidad, la IA sólo acierta más en{" "}
                      {prediction.data.verdict.beaten_ccaa} de las{" "}
                      {prediction.data.verdict.total_ccaa}, y antes de empezar
                      pusimos el listón en {prediction.data.verdict.required}. Por
                      eso aquí no te enseñamos lo que predice la IA: no ha
                      demostrado hacerlo mejor que una regla que cabe en una línea.
                    </>
                  )}
                </p>
              )}
              <p className="layer-note">
                Los datos desde {String(prediction.data.protocol.test_start).slice(0, 4)} los
                guardamos sin tocar, para una prueba final. El detalle técnico está
                en la pestaña Predicción.
              </p>
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
