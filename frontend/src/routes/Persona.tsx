import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { usePersonas, useRedlines } from "../api/hooks";
import { baseline, YEARS } from "../engine/spain";
import { evaluatePersonaReds } from "../engine/redlines";
import { seriesOf, type AnySeriesKey } from "../engine/derived";
import { nf } from "../lib/fmt";
import { Chain } from "../components/Chain";
import { KpiRow, SERIES_FORMAT } from "../components/KpiRow";
import { NarrativeBlock } from "../components/NarrativeBlock";
import { ProjectionChart } from "../components/ProjectionChart";
import { Semaphore } from "../components/Semaphore";
import { Stamp } from "../components/Stamp";
import { SHIPPED_IDS, getPersonaModule } from "../personas/registry";
import { isFresh, kIndex, useScenario, useScenarioStore } from "../state/scenarioStore";

export default function Persona() {
  const { id } = useParams<{ id: string }>();
  const personas = usePersonas();
  const redlines = useRedlines();
  const scn = useScenario();
  const levers = useScenarioStore((s) => s.levers);
  const horizon = useScenarioStore((s) => s.horizon);
  const setHotIds = useScenarioStore((s) => s.setHotIds);
  const card = personas.data?.personas.find((c) => c.id === id);
  const mod = id ? getPersonaModule(id) : undefined;

  useEffect(() => {
    setHotIds(card?.hot ?? []);
    return () => setHotIds([]);
  }, [card, setHotIds]);

  if (personas.isPending) return <p>Cargando perfil…</p>;
  if (personas.isError) return <div className="banner err">Personas no disponibles — el resto de la app sigue funcionando.</div>;
  // The published list is read from the registry, never retyped: adding a
  // persona module is meant to be one MODULES line plus one SHIPPED_IDS entry.
  if (!card || !mod) return <p>Perfil no disponible — perfiles publicados: {SHIPPED_IDS.join(", ")}.</p>;

  const base = baseline();
  const k = kIndex(horizon);
  const fresh = isFresh(levers, horizon);
  const year = horizon;
  // `puntos` periods are string|number — a plain year arrives as a number, a
  // month or quarter as "2021-07"/"2020-Q2". The chart prints them verbatim
  // rather than pretending an index is a year (see ProjectionChart#labels).
  const hist = personas.data.series[card.series_keys[0]];
  const headlineKey = card.headline as AnySeriesKey;
  const headlineDec = SERIES_FORMAT[card.headline]?.dec ?? 1;
  const personaRedLines = card.reds
    .filter((r) => r.k === card.headline && r.thr !== null)
    .map((r) => ({ value: r.thr as number, label: r.t }));
  const globalRedLines = (redlines.data?.redlines ?? [])
    .filter((rl) => rl.series === card.headline)
    .map((rl) => ({ value: rl.threshold, label: rl.label }));

  return (
    <div>
      <div className="head">
        <h1>{card.h1}</h1>
        <Stamp fresh={fresh} year={year} />
        <span className="meta">{card.meta}</span>
      </div>

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
    </div>
  );
}
