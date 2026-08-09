import { useState } from "react";
import type { Levers } from "../engine/levers";
import { runScenario } from "../engine/spain";
import { nf } from "../lib/fmt";

interface FlowLink {
  id: string;
  sourceLabel: string;
  targetLabel: string;
  value: number;
  color: string;
  y0a: number;
  y0b: number;
  y1a: number;
  y1b: number;
}

export function BudgetFlowChart({ levers, horizon = 2030 }: { levers: Levers; horizon?: number }) {
  const [selectedYear, setSelectedYear] = useState<number>(horizon);
  const [hoveredFlow, setHoveredFlow] = useState<string | null>(null);

  const scn = runScenario(levers);
  const yearIdx = Math.max(0, Math.min(24, selectedYear - 2026));

  const gtot = scn.gtot[yearIdx] ?? 45.4;
  const pens = scn.pens[yearIdx] ?? 13.2;
  const edu = scn.edu[yearIdx] ?? 4.1;
  const intr = scn.int[yearIdx] ?? 2.4;
  const saldo = scn.saldo[yearIdx] ?? -3.0;

  const sanidad = 6.8;
  const desempleoInv = Math.max(1.5, (scn.u[yearIdx] ?? 10.1) * 0.25);
  const adminOtros = Math.max(2.0, gtot - (pens + edu + intr + sanidad + desempleoInv));

  const deficit = Math.max(0, -saldo);
  const totalRevenues = Math.max(0.1, gtot - deficit);
  const irpfSoc = totalRevenues * 0.42;
  const ivaEspeciales = totalRevenues * 0.33;
  const cotizaciones = totalRevenues * 0.25;

  // Geometry calculations (SVG 920x520)
  const SVG_H = 400;
  const TOP_Y = 25;
  const GAP_Y = 10;
  const SCALE = SVG_H / (gtot || 1);

  // Left Sources Nodes
  const sources = [
    { id: "irpf", label: "Impuestos Directos (IRPF/Soc.)", val: irpfSoc, color: "#10b981" },
    { id: "iva", label: "Impuestos Indirectos (IVA/Esp.)", val: ivaEspeciales, color: "#0284c7" },
    { id: "cotiz", label: "Cotizaciones Sociales", val: cotizaciones, color: "#8b5cf6" },
    ...(deficit > 0 ? [{ id: "def", label: "Financiación Déficit", val: deficit, color: "#ef4444" }] : []),
  ];

  // Right Targets Nodes
  const targets = [
    { id: "pens", label: "Pensiones y Protec. Social", val: pens, color: "#f97316" },
    { id: "san", label: "Sanidad Pública", val: sanidad, color: "#10b981" },
    { id: "edu", label: "Educación Pública", val: edu, color: "#0284c7" },
    { id: "int", label: "Intereses de Deuda", val: intr, color: "#ef4444" },
    { id: "adm", label: "Inversión y Admón General", val: adminOtros + desempleoInv, color: "#64748b" },
  ];

  // Calculate stacked Positions
  let currentY = TOP_Y;
  const sourcePositions: Record<string, { yStart: number; h: number }> = {};
  sources.forEach((s) => {
    const h = Math.max(16, s.val * SCALE);
    sourcePositions[s.id] = { yStart: currentY, h };
    currentY += h + GAP_Y;
  });

  currentY = TOP_Y;
  const targetPositions: Record<string, { yStart: number; h: number }> = {};
  targets.forEach((t) => {
    const h = Math.max(16, t.val * SCALE);
    targetPositions[t.id] = { yStart: currentY, h };
    currentY += h + GAP_Y;
  });

  // Links distribution
  const linksRaw = [
    { s: "cotiz", t: "pens", val: Math.min(cotizaciones, pens), color: "#8b5cf6" },
    { s: "cotiz", t: "adm", val: Math.max(0, cotizaciones - pens), color: "#8b5cf6" },

    { s: "irpf", t: "pens", val: Math.max(0, pens - cotizaciones), color: "#10b981" },
    { s: "irpf", t: "san", val: sanidad * 0.65, color: "#10b981" },
    { s: "irpf", t: "edu", val: edu * 0.7, color: "#10b981" },
    { s: "irpf", t: "adm", val: Math.max(0, irpfSoc - (pens - cotizaciones) - sanidad * 0.65 - edu * 0.7), color: "#10b981" },

    { s: "iva", t: "san", val: sanidad * 0.35, color: "#0284c7" },
    { s: "iva", t: "edu", val: edu * 0.3, color: "#0284c7" },
    { s: "iva", t: "adm", val: Math.max(0, ivaEspeciales - sanidad * 0.35 - edu * 0.3), color: "#0284c7" },

    ...(deficit > 0 ? [
      { s: "def", t: "int", val: intr, color: "#ef4444" },
      { s: "def", t: "adm", val: Math.max(0, deficit - intr), color: "#ef4444" },
    ] : []),
  ].filter((l) => l.val > 0.05);

  // Compute Ribbon Y-Offsets
  const sourceTracker: Record<string, number> = {};
  const targetTracker: Record<string, number> = {};
  sources.forEach((s) => (sourceTracker[s.id] = sourcePositions[s.id]?.yStart ?? TOP_Y));
  targets.forEach((t) => (targetTracker[t.id] = targetPositions[t.id]?.yStart ?? TOP_Y));

  const links: FlowLink[] = linksRaw.map((l, idx) => {
    const flowH = Math.max(4, l.val * SCALE);

    const y0a = sourceTracker[l.s];
    const y0b = y0a + flowH;
    sourceTracker[l.s] = y0b;

    const y1a = targetTracker[l.t];
    const y1b = y1a + flowH;
    targetTracker[l.t] = y1b;

    const sNode = sources.find((s) => s.id === l.s);
    const tNode = targets.find((t) => t.id === l.t);

    return {
      id: `link-${idx}`,
      sourceLabel: sNode?.label ?? l.s,
      targetLabel: tNode?.label ?? l.t,
      value: l.val,
      color: l.color,
      y0a, y0b, y1a, y1b,
    };
  });

  const X_LEFT = 210;
  const X_RIGHT = 620;
  const X_MID = (X_LEFT + X_RIGHT) / 2;

  return (
    <div className="card" style={{ padding: 18, marginTop: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <div>
          <h4 style={{ margin: 0, fontSize: 17, fontWeight: 800 }}>
            Flujo de Ingresos y Gastos del Estado <small>(Diagrama Sankey Oficial)</small>
          </h4>
          <span style={{ fontSize: 13, color: "var(--muted)" }}>
            Trazabilidad exacta de flujos desde impuestos y recaudación hacia partidas de gasto público en {selectedYear}
          </span>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <label htmlFor="bg-year-select" style={{ fontSize: 13, fontWeight: 700 }}>Año de proyección:</label>
          <select
            id="bg-year-select"
            value={selectedYear}
            onChange={(e) => setSelectedYear(Number(e.target.value))}
            style={{ fontSize: 13.5, padding: "6px 12px", borderRadius: 6, border: "1px solid var(--grid)", background: "var(--surface)", fontWeight: 700 }}
          >
            {[2026, 2030, 2035, 2040, 2045, 2050].map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
      </div>

      <div style={{ position: "relative", width: "100%", overflowX: "auto" }}>
        <svg viewBox="0 0 920 520" style={{ width: "100%", height: "auto", minWidth: 700, overflow: "visible" }}>
          <defs>
            {links.map((l) => (
              <linearGradient key={`grad-${l.id}`} id={`grad-${l.id}`} x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor={l.color} stopOpacity={hoveredFlow === l.id ? 0.85 : 0.45} />
                <stop offset="100%" stopColor={l.color} stopOpacity={hoveredFlow === l.id ? 0.95 : 0.5} />
              </linearGradient>
            ))}
          </defs>

          {/* Render Flow Ribbons */}
          {links.map((l) => {
            const dPath = `M ${X_LEFT} ${l.y0a} C ${X_MID} ${l.y0a}, ${X_MID} ${l.y1a}, ${X_RIGHT} ${l.y1a} L ${X_RIGHT} ${l.y1b} C ${X_MID} ${l.y1b}, ${X_MID} ${l.y0b}, ${X_LEFT} ${l.y0b} Z`;
            const isHovered = hoveredFlow === l.id;
            return (
              <path
                key={l.id}
                d={dPath}
                fill={`url(#grad-${l.id})`}
                stroke={isHovered ? l.color : "none"}
                strokeWidth={isHovered ? 1.5 : 0}
                style={{ cursor: "pointer", transition: "all 150ms ease" }}
                onMouseEnter={() => setHoveredFlow(l.id)}
                onMouseLeave={() => setHoveredFlow(null)}
              >
                <title>{`${l.sourceLabel} ➔ ${l.targetLabel}: ${nf(l.value, 1)} % PIB`}</title>
              </path>
            );
          })}

          {/* Render Left Source Nodes */}
          {sources.map((s) => {
            const pos = sourcePositions[s.id];
            if (!pos) return null;
            return (
              <g key={`src-node-${s.id}`}>
                <rect x={10} y={pos.yStart} width={X_LEFT - 10} height={pos.h} rx={5} fill="var(--surface)" stroke={s.color} strokeWidth={2} />
                <rect x={X_LEFT - 12} y={pos.yStart} width={12} height={pos.h} rx={2} fill={s.color} />
                <text x={20} y={pos.yStart + Math.min(22, pos.h / 2 + 4)} fill="var(--ink)" fontSize="13" fontWeight="800">
                  {s.label}
                </text>
                <text x={20} y={pos.yStart + Math.min(38, pos.h / 2 + 18)} fill={s.color} fontSize="13" fontWeight="800">
                  {nf(s.val, 1)} % PIB
                </text>
              </g>
            );
          })}

          {/* Render Right Target Nodes */}
          {targets.map((t) => {
            const pos = targetPositions[t.id];
            if (!pos) return null;
            return (
              <g key={`tgt-node-${t.id}`}>
                <rect x={X_RIGHT} y={pos.yStart} width={900 - X_RIGHT} height={pos.h} rx={5} fill="var(--surface)" stroke={t.color} strokeWidth={2} />
                <rect x={X_RIGHT} y={pos.yStart} width={12} height={pos.h} rx={2} fill={t.color} />
                <text x={X_RIGHT + 20} y={pos.yStart + Math.min(22, pos.h / 2 + 4)} fill="var(--ink)" fontSize="13" fontWeight="800">
                  {t.label}
                </text>
                <text x={X_RIGHT + 20} y={pos.yStart + Math.min(38, pos.h / 2 + 18)} fill={t.color} fontSize="13" fontWeight="800">
                  {nf(t.val, 1)} % PIB
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "var(--muted)", borderTop: "1px dashed var(--grid)", paddingTop: 10, marginTop: 8 }}>
        <div><b>Recaudación Total:</b> {nf(gtot, 1)} % PIB</div>
        <div><b>Gasto Público Total:</b> {nf(gtot, 1)} % PIB</div>
        <div><b>Déficit / Ajuste:</b> {deficit > 0 ? `+${nf(deficit, 1)} % PIB` : `${nf(saldo, 1)} % PIB`}</div>
      </div>
    </div>
  );
}
