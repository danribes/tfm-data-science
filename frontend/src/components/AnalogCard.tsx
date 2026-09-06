import { useState } from "react";
import type { AnalogMatch } from "../api/types";
import { ProjectionChart } from "./ProjectionChart";
import { AnalogDiffRow } from "./AnalogDiffRow";

const VERDICT_LABEL: Record<string, { text: string; color: string }> = {
  auto:              { text: "AUTO-LIQUIDABLE",   color: "#22c55e" },
  requires_surplus:  { text: "REQUIERE SUPERÁVIT", color: "#ef4444" },
  borderline:        { text: "LÍMITE",             color: "#f59e0b" },
};

function fmt(v: number | null, dec = 1): string {
  return v === null ? "—" : v.toFixed(dec).replace(".", ",");
}

export function AnalogCard({ matches }: { matches: AnalogMatch[] }) {
  const [active, setActive] = useState(0);
  if (!matches.length) return null;
  const m = matches[active];

  const outcomeYears = m.outcome.map((pt) => m.match_year + pt.year_offset);
  const debtOutcome  = m.outcome.map((pt) => pt.debt_gdp ?? 0);
  const rmgOutcome   = m.outcome.map((pt) => pt.r_minus_g ?? 0);

  const verd = VERDICT_LABEL[m.debt_payable_verdict] ?? { text: m.debt_payable_verdict, color: "inherit" };
  const snap = m.match_snapshot;
  const rmg  = snap.r_minus_g ?? 0;

  const fallbackNarrative =
    m.narrative ??
    `${m.country_name} en ${m.match_year}: datos históricos disponibles para ${m.outcome.filter((p) => !p.truncated).length} años. ` +
    `Diferencias estructurales: ${m.diffs.filter((d) => d.direction === "diverge").map((d) => d.label).join(", ") || "ninguna relevante"}.`;

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
            distancia: {m.distance.toFixed(2)} · palanca dominante: {m.dominant_lever}
          </span>
        </div>
        <span
          style={{
            fontSize: 11,
            fontWeight: 700,
            padding: "2px 8px",
            borderRadius: 4,
            background: verd.color + "22",
            color: verd.color,
            border: `1px solid ${verd.color}`,
          }}
        >
          {verd.text}
        </span>
      </div>

      {/* Snapshot KPIs */}
      <div style={{ display: "flex", gap: 16, marginTop: 10, flexWrap: "wrap" }}>
        {[
          ["Deuda", snap.debt_gdp, "%PIB"],
          ["Saldo primario", snap.primary_balance_gdp, "%PIB"],
          ["Bono 10A", snap.interest_rate_10y, "%"],
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
      <div style={{ marginTop: 6, fontSize: 13 }}>
        <strong>r − g = {rmg >= 0 ? "+" : ""}{fmt(rmg)}</strong>
        {" "}→{" "}
        <span style={{ color: verd.color }}>
          {m.debt_payable_verdict === "auto"
            ? "deuda se autoliquida (r < g)"
            : m.debt_payable_verdict === "requires_surplus"
            ? "requiere superávit primario (r > g)"
            : "en el límite (|r − g| < 0,5 pp)"}
        </span>
      </div>

      {/* Trajectory chart */}
      <h5 style={{ marginTop: 14, marginBottom: 4 }}>Trayectoria ({m.outcome.length} años)</h5>
      <ProjectionChart
        years={outcomeYears}
        baseline={debtOutcome}
        scenario={debtOutcome}
        unit="%PIB"
        dec={1}
        height={180}
        labels={outcomeYears.map(String)}
      />
      <div style={{ marginTop: 8 }}>
        <span style={{ fontSize: 12, color: "var(--muted)" }}>r − g histórico</span>
        <ProjectionChart
          years={outcomeYears}
          baseline={rmgOutcome}
          scenario={rmgOutcome}
          unit="pp"
          dec={2}
          height={120}
          labels={outcomeYears.map(String)}
        />
      </div>
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
              <th style={{ textAlign: "right" }}>Efecto</th>
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
