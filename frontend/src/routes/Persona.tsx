import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useEvidence, usePersonas, useRedlines } from "../api/hooks";
import { baseline, YEARS } from "../engine/spain";
import { evaluatePersonaReds } from "../engine/redlines";
import { seriesOf, type AnySeriesKey } from "../engine/derived";
import { nf } from "../lib/fmt";
import { AnswerPanel } from "../components/AnswerPanel";
import { Chain } from "../components/Chain";
import { KpiRow, SERIES_FORMAT } from "../components/KpiRow";
import { NarrativeBlock } from "../components/NarrativeBlock";
import { ProjectionChart } from "../components/ProjectionChart";
import { Semaphore } from "../components/Semaphore";
import { Stamp } from "../components/Stamp";
import { SHIPPED_IDS, getPersonaModule } from "../personas/registry";
import { matchQuestion, questionsFor } from "../personas/questions";
import { isFresh, kIndex, useScenario, useScenarioStore } from "../state/scenarioStore";

export default function Persona() {
  const { id } = useParams<{ id: string }>();
  const personas = usePersonas();
  const redlines = useRedlines();
  const evidence = useEvidence();
  const scn = useScenario();
  const levers = useScenarioStore((s) => s.levers);
  const horizon = useScenarioStore((s) => s.horizon);
  const setHotIds = useScenarioStore((s) => s.setHotIds);
  const setChartsHidden = useScenarioStore((s) => s.setChartsHidden);
  const card = personas.data?.personas.find((c) => c.id === id);
  const mod = id ? getPersonaModule(id) : undefined;

  const questions = questionsFor(id ?? "");
  const [askedId, setAskedId] = useState<string | null>(null);
  const [typed, setTyped] = useState("");
  const [showAll, setShowAll] = useState(false);
  const [noMatch, setNoMatch] = useState(false);
  const asked = questions.find((q) => q.id === askedId) ?? null;

  // A new profile is a new conversation; carrying the previous answer over
  // would attach it to a persona whose question set may not contain it.
  useEffect(() => { setAskedId(null); setTyped(""); setShowAll(false); setNoMatch(false); }, [id]);

  useEffect(() => {
    // When a question is on screen, the levers it names are the ones worth
    // reaching for; otherwise fall back to the profile's own hot list.
    setHotIds(asked ? asked.levers : (card?.hot ?? []));
    return () => setHotIds([]);
  }, [card, asked, setHotIds]);

  // Nothing is plotted until a question is asked, so the shell explainer has
  // no figure to caption and stays out of the way.
  const bareLanding = questions.length > 0 && !asked && !showAll;
  useEffect(() => {
    setChartsHidden(bareLanding);
    return () => setChartsHidden(false);
  }, [bareLanding, setChartsHidden]);

  if (personas.isPending) return <p>Cargando perfil…</p>;
  if (personas.isError) return <div className="banner err">Personas no disponibles — el resto de la app sigue funcionando.</div>;
  if (!card || !mod) return <p>Perfil no disponible — perfiles publicados: {SHIPPED_IDS.join(", ")}.</p>;

  const base = baseline();
  const k = kIndex(horizon);
  const fresh = isFresh(levers, horizon);
  const year = horizon;
  const hist = personas.data.series[card.series_keys[0]];
  const headlineKey = card.headline as AnySeriesKey;
  const headlineDec = SERIES_FORMAT[card.headline]?.dec ?? 1;
  const personaRedLines = card.reds
    .filter((r) => r.k === card.headline && r.thr !== null)
    .map((r) => ({ value: r.thr as number, label: r.t }));
  const globalRedLines = (redlines.data?.redlines ?? [])
    .filter((rl) => rl.series === card.headline)
    .map((rl) => ({ value: rl.threshold, label: rl.label }));

  const estimated = (evidence.data?.comparisons ?? []).map((cmp) => ({
    name: cmp.constant,
    value: cmp.coef,
    ci_low: cmp.ci_low,
    ci_high: cmp.ci_high,
    calibrated_v16: cmp.calibrated,
  }));

  /** Match free text to the question set. Nothing is answered that was not
   *  bound to a series: a scenario engine cannot answer an arbitrary question,
   *  and guessing is how a tool starts making things up.
   *
   *  Accents are stripped on both sides. Spanish is routinely typed without
   *  them, and «cuanto costara» failing to match «¿Cuánto costará…» is the
   *  normal case, not an edge one. */
  const submitTyped = () => {
    const hit = matchQuestion(typed, questions);
    if (hit) {
      setAskedId(hit.id);
      setTyped("");
      setNoMatch(false);
    } else {
      // Saying nothing looks identical to a broken button. The reader has to
      // learn that this box answers a bounded set, and the only honest moment
      // to teach that is when their question falls outside it.
      setNoMatch(true);
    }
  };

  // Profiles without a question set keep the original full page.
  const conversational = questions.length > 0;

  return (
    <div>
      <div className="head">
        <h1>{card.h1}</h1>
        <Stamp fresh={fresh} year={year} />
        <span className="meta">{card.meta}</span>
      </div>

      {conversational && (
        <div className="card ask-card">
          <form
            className="consulta-form"
            onSubmit={(e) => { e.preventDefault(); submitTyped(); }}
          >
            <input
              className="consulta-input"
              value={typed}
              onChange={(e) => { setTyped(e.target.value); setNoMatch(false); }}
              placeholder={`Pregunta sobre ${card.h1.toLowerCase()}…`}
            />
            <button type="submit" className="consulta-btn" disabled={typed.trim().length < 3}>
              Preguntar
            </button>
          </form>
          {noMatch && (
            <p className="ask-nomatch">
              No sé responder a eso con este motor. Calcula escenarios sobre un
              conjunto acotado de series, así que sólo puedo contestar a lo que
              sale de él — elige una de estas:
            </p>
          )}
          <ul className="consulta-examples">
            {questions.map((q) => (
              <li key={q.id}>
                <button
                  type="button"
                  className={q.id === askedId ? "example-chip on" : "example-chip"}
                  onClick={() => { setAskedId(q.id); setNoMatch(false); }}
                >
                  {q.text}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {conversational && asked && (
        <AnswerPanel
          q={asked}
          all={questions}
          scn={scn}
          base={base}
          k={k}
          year={year}
          estimated={estimated}
          onAsk={setAskedId}
        />
      )}

      {conversational && !asked && (
        <p className="ask-hint">
          Todavía no hay nada proyectado: las palancas de la izquierda están en
          su valor observado del vintage {personas.data.vintage}. Elige una
          pregunta y verás el número que sale del motor, la gráfica de la que
          viene, cómo se calcula y qué no sabe. Sólo eso — el panel completo del
          perfil, con todos los indicadores a la vez, sigue disponible debajo.
        </p>
      )}

      {conversational && (
        <button type="button" className="show-all" onClick={() => setShowAll((v) => !v)}>
          {showAll ? "▾ ocultar el panel completo" : "▸ ver el panel completo del perfil"}
        </button>
      )}

      {(!conversational || showAll) && (
        <>
          <KpiRow outs={card.outs} scn={scn} base={base} k={k} fresh={fresh} year={year} personaReds={card.reds} />

          <div className="row2">
            <div className="card">
              <h4>Histórico <small>{hist?.fuente ?? "serie no disponible"}</small></h4>
              {hist ? (
                <ProjectionChart
                  years={hist.puntos.map((_, i) => i)}
                  labels={hist.puntos.map(([p]) => String(p))}
                  baseline={hist.puntos.map(([, v]) => v)}
                  scenario={hist.puntos.map(([, v]) => v)}
                  dec={2}
                />
              ) : (
                <div className="banner err">Serie histórica no disponible</div>
              )}
            </div>
            <div className="card">
              <h4>Proyección 2026–2050 <small>{card.outs.find((o) => o.k === card.headline)?.lab ?? card.headline} · base punteada vs escenario</small></h4>
              <ProjectionChart
                years={YEARS}
                baseline={seriesOf(base, headlineKey)}
                scenario={seriesOf(scn, headlineKey)}
                redLines={[...personaRedLines, ...globalRedLines.filter((g) => !personaRedLines.some((p) => p.value === g.value))]}
                unit={SERIES_FORMAT[card.headline]?.unit ?? ""}
                dec={headlineDec}
              />
            </div>
          </div>

          <div className="row3">
            <div className="card">
              <h4>Semáforo del perfil <small>umbrales de presentación — no son las líneas rojas globales</small></h4>
              <Semaphore
                items={evaluatePersonaReds(card.reds, scn, k).map((r) => ({
                  title: r.t,
                  valueText: r.value === null ? "s/d" : nf(r.value, r.d ?? 1),
                  status: r.status,
                  note: r.x,
                }))}
              />
            </div>
            <div className="card">
              <h4>Transmisión <small>de la palanca al bolsillo</small></h4>
              <Chain specs={mod.chains} scn={scn} base={base} k={k} />
            </div>
            <div className="card">
              <NarrativeBlock text={mod.narr(scn, k, year)} cite={`trazado a ${mod.cite}`} />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
