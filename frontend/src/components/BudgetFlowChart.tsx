import { useEffect, useState } from "react";
import type { Levers } from "../engine/levers";
import { runScenario } from "../engine/spain";
import { nf } from "../lib/fmt";
import { budgetFlows } from "./fiscalFlows";
import { HowToRead } from "./HowToRead";
import { GTOT_RECORD } from "../lib/historico";

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

  useEffect(() => setSelectedYear(horizon), [horizon]);
  const budget = budgetFlows(scn, yearIdx);
  if (!budget) {
    return <div className="card" role="status">Desglose presupuestario no disponible: las partidas del escenario no forman un presupuesto con importes no negativos.</div>;
  }
  const { sources, targets, links: linksRaw, revenues, spending, balance } = budget;
  // How much more revenue the accounts need than in the first year: spending
  // follows pensions and interest, the deficit comes from the central path.
  const revenueGap = revenues - (scn.gtot[0] + scn.saldo[0]);

  // Exact proportional widths. Sources and uses have equal totals; the
  // individual ribbons are a synthetic allocation, not earmarked tax receipts.
  const SVG_H = 400;
  const TOP_Y = 25;
  const GAP_Y = 10;
  const SCALE = SVG_H / budget.total;

  // Calculate stacked Positions
  let currentY = TOP_Y;
  const sourcePositions: Record<string, { yStart: number; h: number }> = {};
  sources.forEach((s) => {
    const h = s.val * SCALE;
    sourcePositions[s.id] = { yStart: currentY, h };
    currentY += h + GAP_Y;
  });

  currentY = TOP_Y;
  const targetPositions: Record<string, { yStart: number; h: number }> = {};
  targets.forEach((t) => {
    const h = t.val * SCALE;
    targetPositions[t.id] = { yStart: currentY, h };
    currentY += h + GAP_Y;
  });

  // Compute Ribbon Y-Offsets
  const sourceTracker: Record<string, number> = {};
  const targetTracker: Record<string, number> = {};
  sources.forEach((s) => (sourceTracker[s.id] = sourcePositions[s.id]?.yStart ?? TOP_Y));
  targets.forEach((t) => (targetTracker[t.id] = targetPositions[t.id]?.yStart ?? TOP_Y));

  const links: FlowLink[] = linksRaw.map((l, idx) => {
    const flowH = l.val * SCALE;

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

  // Where spending passes its 2020 record in the right-hand stack: walk the
  // spending nodes (not a surplus) until their running total reaches the
  // record, and interpolate inside that node. Everything below it is spending
  // Spain has never had.
  let recordY: number | null = null;
  let spendEnd = TOP_Y;
  if (spending > GTOT_RECORD.value) {
    let cum = 0;
    for (const t of targets) {
      if (t.id === "surplus") continue;
      const pos = targetPositions[t.id];
      if (!pos) continue;
      if (recordY === null && cum + t.val >= GTOT_RECORD.value) {
        recordY = pos.yStart + (GTOT_RECORD.value - cum) * SCALE;
      }
      cum += t.val;
      spendEnd = pos.yStart + pos.h;
    }
  }

  const X_LEFT = 210;
  const X_RIGHT = 620;
  const X_MID = (X_LEFT + X_RIGHT) / 2;

  return (
    <div className="card" style={{ padding: 18, marginTop: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <div>
          <h4 style={{ margin: 0, fontSize: 17, fontWeight: 800 }}>
            Presupuesto del escenario <small>(esquema ilustrativo)</small>
          </h4>
          <span style={{ fontSize: 13, color: "var(--muted)" }}>
            Importes del modelo en {selectedYear}; conexiones proporcionales sintéticas, sin atribuir impuestos a gastos concretos.
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

      <HowToRead>
        <p>
          Adónde va el dinero público en el año que elijas, en % del PIB. A la
          izquierda, de dónde sale: lo que se recauda con impuestos y cotizaciones,
          y lo que falta, que se pide prestado (el déficit). A la derecha, en qué se
          gasta: pensiones, sueldos públicos, intereses de la deuda… Cuanto más
          gruesa es una banda, más dinero. Es un esquema: no dice qué impuesto paga
          qué gasto.
        </p>
      </HowToRead>

      {/* Pensiones e intereses evolucionan y el gasto total ya crece con
          ellos (spain.ts), así que las partidas no pueden sumar más que el
          total. El aviso queda por si un cambio del motor lo rompe: callarlo
          sería peor que enseñarlo. */}
      {budget.exceso > 0.005 && (
        <div className="banner" style={{ fontSize: 12.5, fontWeight: 400, marginBottom: 14 }}>
          Las partidas suman {nf(budget.identificado, 1)} % del PIB,{" "}
          {nf(budget.exceso, 1)} más que el gasto total del escenario. Pensiones e intereses
          evolucionan con la demografía y con la deuda; las otras cinco partidas se quedan en
          su valor observado. Cada partida es correcta; su suma, en este año, no cuadra con el
          total.
        </div>
      )}
      {revenueGap > 0.5 && (
        <p className="muted" style={{ fontSize: 13, margin: "0 0 12px" }}>
          En {selectedYear} el gasto total crece con las pensiones y los intereses, y el
          déficit del escenario crece menos que eso: para que las cuentas cuadren, los
          ingresos tendrían que subir unos {nf(revenueGap, 1)} puntos de PIB respecto a
          2026. El modelo no decide de dónde saldrían.
        </p>
      )}

      {recordY !== null && (
        <p className="danger-note" role="note">
          <span aria-hidden="true">⚠</span>{" "}
          En {selectedYear} el gasto público llegaría al {nf(spending, 1)} % del PIB, por
          encima de su récord: el {nf(GTOT_RECORD.value, 1)} % de {GTOT_RECORD.year}, en plena
          pandemia. La zona roja de la derecha es el gasto que pasa de ese récord, empujado por
          las pensiones y los intereses de la deuda. Cada punto de más habría que pagarlo con
          impuestos o con más deuda.
        </p>
      )}

      <div style={{ position: "relative", width: "100%", overflowX: "auto" }}>
        <svg role="img" aria-label={`Esquema presupuestario ilustrativo de ${selectedYear}`} viewBox="0 0 920 520" style={{ width: "100%", height: "auto", minWidth: 700, overflow: "visible" }}>
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
                <text x={20} y={pos.yStart + Math.min(18, pos.h / 2 + 4)} fill="var(--ink)" fontSize="13" fontWeight="800">
                  {pos.h < 30 ? `${s.label}: ${nf(s.val, 1)} % PIB` : s.label}
                </text>
                {pos.h >= 30 && <text x={20} y={pos.yStart + Math.min(34, pos.h - 4)} fill={s.color} fontSize="13" fontWeight="800">
                  {nf(s.val, 1)} % PIB
                </text>}
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
                <text x={X_RIGHT + 20} y={pos.yStart + Math.min(18, pos.h / 2 + 4)} fill="var(--ink)" fontSize="13" fontWeight="800">
                  {pos.h < 30 ? `${t.label}: ${nf(t.val, 1)} % PIB` : t.label}
                </text>
                {pos.h >= 30 && <text x={X_RIGHT + 20} y={pos.yStart + Math.min(34, pos.h - 4)} fill={t.color} fontSize="13" fontWeight="800">
                  {nf(t.val, 1)} % PIB
                </text>}
              </g>
            );
          })}

          {/* The danger zone: spending past its 2020 record, tinted, and the
              record itself as a dashed line with its label. */}
          {recordY !== null && (
            <g data-testid="record-zone" pointerEvents="none">
              <rect x={X_RIGHT} y={recordY} width={900 - X_RIGHT} height={Math.max(0, spendEnd - recordY)}
                fill="var(--st-crossed)" fillOpacity={0.14} />
              <line x1={X_RIGHT - 40} y1={recordY} x2={908} y2={recordY}
                stroke="var(--st-crossed)" strokeWidth={2} strokeDasharray="6 4" />
              <text x={X_RIGHT - 46} y={recordY + 4} textAnchor="end" fill="var(--st-crossed)"
                fontSize="13" fontWeight="800" stroke="var(--surface)" strokeWidth={4} paintOrder="stroke">
                ⚠ récord {GTOT_RECORD.year}: {nf(GTOT_RECORD.value, 1)} % del PIB
              </text>
            </g>
          )}
        </svg>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "var(--muted)", borderTop: "1px dashed var(--grid)", paddingTop: 10, marginTop: 8 }}>
        <div><b>Ingresos implícitos:</b> {nf(revenues, 1)} % PIB</div>
        <div><b>Gasto total:</b> {nf(spending, 1)} % PIB</div>
        <div><b>Saldo total:</b> {nf(balance, 1)} % PIB</div>
      </div>
    </div>
  );
}
