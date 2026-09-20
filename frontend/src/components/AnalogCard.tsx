import { useState } from "react";
import type { AnalogMatch } from "../api/types";
import { ProjectionChart } from "./ProjectionChart";
import { AnalogDiffRow } from "./AnalogDiffRow";
import { LEVER_SPECS } from "../engine/levers";

function fmt(v: number | null | undefined, dec = 1): string {
  return v == null ? "—" : v.toFixed(dec).replace(".", ",");
}

export function AnalogCard({ matches }: { matches: AnalogMatch[] }) {
  const [active, setActive] = useState(0);
  if (!matches.length) return null;
  const m = matches[active] ?? matches[0];

  const validOutcome = m.outcome;
  const outcomeYears = validOutcome.map((pt) => m.match_year + pt.year_offset);
  const debtOutcome  = validOutcome.map((pt) => pt.debt_gdp);
  const snap = m.match_snapshot;

  const fallbackNarrative =
    m.narrative ??
    `${m.country_name} en ${m.match_year}: datos históricos disponibles para ${m.outcome.filter((p) => !p.truncated).length} años. ` +
    `Diferencias estructurales: ${m.diffs.filter((d) => d.direction === "diverge").map((d) => d.label).join(", ") || "sin diferencias documentadas"}.`;

  return (
    <div className="card" style={{ marginTop: 12 }}>
      {/* Tab selector */}
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        {matches.map((mx, i) => (
          <button
            key={mx.rank}
            role="tab"
            aria-selected={i === active}
            onClick={() => setActive(i)}
            style={{
              padding: "4px 12px",
              borderRadius: 6,
              border: i === active ? "2px solid var(--accent, #3b82f6)" : "1px solid var(--border, #d1d5db)",
              background: i === active ? "var(--accent, #3b82f6)" : "transparent",
              color: i === active ? "#fff" : "inherit",
              cursor: "pointer",
              fontSize: 13,
              fontWeight: 600,
            }}
          >
            #{mx.rank} {mx.country_name} · {mx.match_year}
          </button>
        ))}
      </div>

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h4 style={{ margin: 0 }}>{m.country_name} · {m.match_year}</h4>
          <span className="meta" style={{ fontSize: 12 }}>
            distancia: {m.distance.toFixed(2)} · palanca dominante: {m.dominant_lever
              ? (LEVER_SPECS.find(s => s.id === m.dominant_lever)?.nm ?? m.dominant_lever)
              : "—"}
          </span>
        </div>
        <span className="meta">Similitud descriptiva</span>
      </div>

      {/* Snapshot KPIs */}
      <div style={{ display: "flex", gap: 16, marginTop: 10, flexWrap: "wrap" }}>
        {[
          ["Deuda", snap.debt_gdp, "%PIB"],
          ["Saldo total", snap.overall_balance_gdp, "%PIB"],
          ["Tipo de préstamo bancario (contexto)", snap.lending_rate, "%"],
          ["Crec. real", snap.gdp_growth, "%"],
          ["Paro", snap.unemployment, "%"],
          ["Inflación", snap.inflation, "%"],
        ].map(([label, val, unit]) => (
          <div key={String(label)} className="kpi-mini" style={{ textAlign: "center", minWidth: 80 }}>
            <div style={{ fontSize: 18, fontWeight: 700 }}>{fmt(val as number | null)}</div>
            <div style={{ fontSize: 11, color: "var(--muted)" }}>{String(label)} ({unit})</div>
          </div>
        ))}
      </div>
      <p className="src">La sostenibilidad de la deuda no se estima: el panel carece de
        un coste efectivo soberano comparable. El tipo de préstamo bancario no entra en la búsqueda.</p>

      {/* Trajectory chart */}
      <h5 style={{ marginTop: 14, marginBottom: 4 }}>Trayectoria ({m.outcome.length} años)</h5>
      <ProjectionChart
        historical
        years={outcomeYears}
        baseline={debtOutcome}
        scenario={debtOutcome}
        unit="%PIB"
        dec={1}
        height={180}
        labels={outcomeYears.map(String)}
      />
      {m.outcome_truncated && (
        <p style={{ fontSize: 12, color: "var(--muted)", marginTop: 4 }}>
          ⚠ Datos disponibles solo hasta {Math.max(...m.outcome.filter((p) => !p.truncated).map((p) => m.match_year + p.year_offset), m.match_year)}. Puntos restantes sin datos.
        </p>
      )}

      {/* Structural diffs */}
      <h5 style={{ marginTop: 16, marginBottom: 4 }}>Diferencias estructurales</h5>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ color: "var(--muted)", fontSize: 11 }}>
              <th />
              <th style={{ textAlign: "left" }}>Dimensión</th>
              <th style={{ textAlign: "right" }}>España</th>
              <th style={{ textAlign: "right" }}>Análogo</th>
              <th style={{ textAlign: "right" }}>Comparación descriptiva</th>
            </tr>
          </thead>
          <tbody>
            {m.diffs.map((d) => <AnalogDiffRow key={d.dimension} diff={d} />)}
          </tbody>
        </table>
      </div>

      {/* Narrative */}
      <h5 style={{ marginTop: 14, marginBottom: 4 }}>Valoración</h5>
      <p style={{ fontSize: 13, lineHeight: 1.55 }}>{fallbackNarrative}</p>
    </div>
  );
}
