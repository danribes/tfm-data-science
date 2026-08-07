import { Link } from "react-router-dom";
import { usePersonas, useRedlines, useVintage } from "../api/hooks";
import { baseline } from "../engine/spain";
import { evaluateRedlines } from "../engine/redlines";
import { allAtBase } from "../engine/levers";
import { nf, sg } from "../lib/fmt";
import { Semaphore } from "../components/Semaphore";
import { Stamp } from "../components/Stamp";
import { SERIES_FORMAT, UP_IS_BAD } from "../components/KpiRow";
import { kIndex, useScenario, useScenarioStore } from "../state/scenarioStore";
import { SHIPPED_IDS } from "../personas/registry";

const HEADLINES: { k: "b" | "saldo" | "u" | "pi"; lab: string; at2050?: boolean }[] = [
  { k: "b", lab: "Deuda 2050", at2050: true },
  { k: "saldo", lab: "Saldo público" },
  { k: "u", lab: "Paro" },
  { k: "pi", lab: "IPCA" },
];

export default function Inicio() {
  const vintage = useVintage();
  const redlines = useRedlines();
  const personas = usePersonas();
  const scn = useScenario();
  const levers = useScenarioStore((s) => s.levers);
  const horizon = useScenarioStore((s) => s.horizon);
  const k = kIndex(horizon);
  const base = baseline();
  const fresh = allAtBase(levers) && horizon === 2026;

  return (
    <div>
      <div className="head">
        <h1>España en escenarios</h1>
        <Stamp fresh={fresh} year={horizon} />
        {vintage.isSuccess ? (
          <span className="meta">vintage {vintage.data.vintage} · {vintage.data.n_files} fuentes congeladas</span>
        ) : vintage.isError ? (
          <span className="meta">cobertura no disponible</span>
        ) : null}
      </div>

      <div className="outs" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
        {HEADLINES.map(({ k: key, lab, at2050 }) => {
          const i = at2050 ? 24 : k;
          const f = SERIES_FORMAT[key];
          const delta = scn[key][i] - base[key][i];
          const cls = Math.abs(delta) <= 1e-9 ? "" : (delta > 0) === UP_IS_BAD.has(key) ? "bad" : "good";
          return (
            <div className="out" key={key}>
              <div className="o-label">{lab}</div>
              <div className="o-val">{nf(scn[key][i], f.dec)} <small>{f.unit}</small></div>
              <div className={`o-delta ${cls}`}>{sg(delta, f.dec)} vs base</div>
            </div>
          );
        })}
      </div>

      <div className="card">
        <h4>Líneas rojas <small>evaluadas en {horizon} · umbrales v12 con fuente</small></h4>
        {redlines.isSuccess ? (
          <Semaphore
            items={evaluateRedlines(redlines.data.redlines, scn, k).map((r) => ({
              title: r.label,
              valueText: nf(r.value, SERIES_FORMAT[r.series]?.dec ?? 1),
              status: r.status,
              note: r.source,
            }))}
          />
        ) : redlines.isError ? (
          <div className="banner err">Líneas rojas no disponibles</div>
        ) : null}
      </div>

      <div className="row2">
        {(personas.data?.personas ?? [])
          .filter((c) => SHIPPED_IDS.includes(c.id))
          .map((c) => (
            <Link key={c.id} to={`/persona/${c.id}`} className="card" style={{ textDecoration: "none", color: "inherit" }}>
              <h4>{c.pill}</h4>
              <span style={{ fontSize: 12, color: "var(--ink-2)" }}>{c.h1}</span>
            </Link>
          ))}
        {personas.isError && <div className="banner err">Personas no disponibles</div>}
      </div>
    </div>
  );
}
