import { useState } from "react";
import type { Levers } from "../engine/levers";
import { runScenario } from "../engine/spain";
import { nf } from "../lib/fmt";

export function DebtAmortizationFlowChart({ levers, horizon = 2030 }: { levers: Levers; horizon?: number }) {
  const [selectedYear, setSelectedYear] = useState<number>(horizon);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  const scn = runScenario(levers);
  const yearIdx = Math.max(0, Math.min(24, selectedYear - 2026));

  const b = scn.b[yearIdx] ?? 105.6;
  const bPrev = yearIdx > 0 ? (scn.b[yearIdx - 1] ?? 105.6) : 105.6;
  const deltaB = b - bPrev;
  const isDeficit = deltaB > 0.001;
  const isSuperavit = deltaB < -0.001;

  const gtot = scn.gtot[yearIdx] ?? 45.4;
  const saldo = scn.saldo[yearIdx] ?? -3.0;
  const rawDeficit = Math.max(0, -saldo);

  // Base Ordinary Revenues & Expenses
  const ordinaryRevenues = Math.max(0.1, gtot - rawDeficit);

  // Geometry (SVG 1000x640)
  const SVG_W = 1000;
  const SCALE = 2.2; // 2.2px per % GDP

  const X_LEFT = 20;
  const W_NODE = 280;
  const X_RIGHT = SVG_W - W_NODE - 20; // 700
  const X_MID = (X_LEFT + W_NODE + X_RIGHT) / 2;

  // Box heights
  const H_DEBT_START = Math.max(100, bPrev * SCALE);
  const H_DEBT_END = Math.max(100, b * SCALE);
  const H_REVENUES = Math.max(90, ordinaryRevenues * SCALE);
  const H_BASE_EXPENSES = Math.max(90, ordinaryRevenues * SCALE);
  const H_DEFICIT_COMPARTMENT = Math.max(34, Math.abs(deltaB) * SCALE);
  const H_TOTAL_EXPENSES = H_BASE_EXPENSES + H_DEFICIT_COMPARTMENT;

  // Vertical offsets
  const Y_DEBT_START = 30;
  const Y_REVENUES = Y_DEBT_START + H_DEBT_START + 30;

  const Y_DEBT_END = 30;
  const Y_EXPENSES = Y_DEBT_END + H_DEBT_END + 30;
  const Y_DEFICIT_COMPARTMENT = Y_EXPENSES + H_BASE_EXPENSES;

  const debtPctBar = Math.min(100, (b / 150) * 100);

  return (
    <div className="card" style={{ padding: 20, marginTop: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <div>
          <h4 style={{ margin: 0, fontSize: 17, fontWeight: 800 }}>
            Diagrama de Flujo Presupuestario y Acumulación de Deuda
          </h4>
          <span style={{ fontSize: 13, color: "var(--muted)" }}>
            Mapeo del gasto total que engloba el déficit ({nf(ordinaryRevenues, 1)} % + {nf(Math.abs(deltaB), 1)} % PIB) y su incorporación a la Deuda Viva en {selectedYear}
          </span>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <label htmlFor="flow-year-select" style={{ fontSize: 13, fontWeight: 700 }}>Año de proyección:</label>
          <select
            id="flow-year-select"
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

      {/* --- Dynamic Fiscal Explanation Banner --- */}
      {isDeficit ? (
        <div style={{ background: "var(--chip-warn)", border: "1px solid var(--div-neg)", borderRadius: 8, padding: 12, marginBottom: 14, fontSize: 13.5, color: "var(--div-neg)", fontWeight: 700 }}>
          📌 En {selectedYear}, la caja <b>EXPENSES</b> engloba los gastos totales (<b>{nf(ordinaryRevenues, 1)} % + {nf(deltaB, 1)} % del PIB</b>). El compartimento inferior punteado representa la fracción del déficit, conectado por la flecha curva con la etiqueta <b>NEW DEBT</b>.
        </div>
      ) : isSuperavit ? (
        <div style={{ background: "var(--st-safe-bg)", border: "1px solid var(--good)", borderRadius: 8, padding: 12, marginBottom: 14, fontSize: 13.5, color: "var(--good)", fontWeight: 700 }}>
          ✅ En {selectedYear}, el superávit presupuestario de <b>-{nf(-deltaB, 1)} % del PIB</b> se destina a la caja de amortización.
        </div>
      ) : null}

      {/* --- Macro Scale Bar: Deuda vs PIB --- */}
      <div style={{ background: "var(--surface)", border: "1px solid var(--grid)", borderRadius: 8, padding: 14, marginBottom: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
          <div style={{ fontSize: 14, fontWeight: 800, color: "var(--ink)" }}>
            Stock Total de Deuda Viva ({nf(b, 1)} % PIB) frente al PIB Nominal Anual (100 % PIB)
          </div>
          <div style={{ fontSize: 14, fontWeight: 800, color: b > 100 ? "var(--div-neg)" : "var(--good)" }}>
            Ratio Deuda/PIB: {nf(b, 1)} % ({nf((b / 100), 2)}x PIB)
          </div>
        </div>

        <div style={{ position: "relative", height: 18, background: "var(--grid)", borderRadius: 6, overflow: "hidden" }}>
          <div style={{ position: "absolute", left: `${(100 / 150) * 100}%`, top: 0, bottom: 0, width: 3, background: "var(--ink)", zIndex: 10 }} />
          <div
            style={{
              position: "absolute",
              left: 0, top: 0, bottom: 0,
              width: `${debtPctBar}%`,
              background: b > 100 ? "var(--div-neg)" : "var(--s1)",
              opacity: 0.85,
              borderRadius: "6px 0 0 6px",
              transition: "width 200ms ease",
            }}
          />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11.5, color: "var(--muted)", marginTop: 4 }}>
          <span>0 % PIB</span>
          <span><b>Límite 100 % PIB (PIB Anual de España)</b></span>
          <span>150 % PIB</span>
        </div>
      </div>

      {/* --- Hand-Drawn Flow Replica SVG Diagram --- */}
      <div style={{ position: "relative", width: "100%", overflowX: "auto" }}>
        <svg viewBox="0 0 1000 640" style={{ width: "100%", height: "auto", minWidth: 800, overflow: "visible" }}>
          <defs>
            {/* Arrow Marker Definitions */}
            <marker id="arrow-red" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#ef4444" />
            </marker>
            <marker id="arrow-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981" />
            </marker>

            {/* Gradient Streams */}
            <linearGradient id="grad-debt" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.45" />
              <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.5" />
            </linearGradient>
            <linearGradient id="grad-rev" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.45" />
              <stop offset="100%" stopColor="#0284c7" stopOpacity="0.5" />
            </linearGradient>
          </defs>

          {/* Flow Ribbon 1: DEBT (Start) -> DEBT (End) */}
          <path
            d={`M ${X_LEFT + W_NODE} ${Y_DEBT_START + 20} C ${X_MID} ${Y_DEBT_START + 20}, ${X_MID} ${Y_DEBT_END + 20}, ${X_RIGHT} ${Y_DEBT_END + 20} L ${X_RIGHT} ${Y_DEBT_END + H_DEBT_END - 20} C ${X_MID} ${Y_DEBT_END + H_DEBT_END - 20}, ${X_MID} ${Y_DEBT_START + H_DEBT_START - 20}, ${X_LEFT + W_NODE} ${Y_DEBT_START + H_DEBT_START - 20} Z`}
            fill="url(#grad-debt)"
            stroke="#8b5cf6"
            strokeWidth="1.5"
            style={{ opacity: hoveredNode === "debt" ? 0.9 : 0.6, transition: "opacity 150ms ease" }}
          />

          {/* Flow Ribbon 2: REVENUES -> EXPENSES */}
          <path
            d={`M ${X_LEFT + W_NODE} ${Y_REVENUES + 15} C ${X_MID} ${Y_REVENUES + 15}, ${X_MID} ${Y_EXPENSES + 15}, ${X_RIGHT} ${Y_EXPENSES + 15} L ${X_RIGHT} ${Y_EXPENSES + H_BASE_EXPENSES - 15} C ${X_MID} ${Y_EXPENSES + H_BASE_EXPENSES - 15}, ${X_MID} ${Y_REVENUES + H_REVENUES - 15}, ${X_LEFT + W_NODE} ${Y_REVENUES + H_REVENUES - 15} Z`}
            fill="url(#grad-rev)"
            stroke="#0284c7"
            strokeWidth="1.5"
            style={{ opacity: hoveredNode === "rev" ? 0.9 : 0.6, transition: "opacity 150ms ease" }}
          />

          {/* --- LEFT COLUMN BOXES --- */}
          {/* Box 1: DEBT (Start of Year) */}
          <g onMouseEnter={() => setHoveredNode("debt")} onMouseLeave={() => setHoveredNode(null)}>
            <rect x={X_LEFT} y={Y_DEBT_START} width={W_NODE} height={H_DEBT_START} rx={10} fill="var(--surface)" stroke="#8b5cf6" strokeWidth={3} />
            <rect x={X_LEFT} y={Y_DEBT_START} width={W_NODE} height={36} rx={10} fill="#8b5cf6" />
            <text x={X_LEFT + W_NODE / 2} y={Y_DEBT_START + 24} fill="#ffffff" fontSize="16" fontWeight="800" textAnchor="middle">
              DEBT (INICIO DE AÑO)
            </text>
            <text x={X_LEFT + 20} y={Y_DEBT_START + 70} fill="var(--ink)" fontSize="18" fontWeight="800">
              {nf(bPrev, 1)} % PIB
            </text>
            <text x={X_LEFT + 20} y={Y_DEBT_START + 94} fill="var(--muted)" fontSize="13" fontWeight="600">
              Stock de Deuda Viva al inicio del ejercicio
            </text>
          </g>

          {/* Box 2: REVENUES (Itemized Text Removed as Requested) */}
          <g onMouseEnter={() => setHoveredNode("rev")} onMouseLeave={() => setHoveredNode(null)}>
            <rect x={X_LEFT} y={Y_REVENUES} width={W_NODE} height={H_REVENUES} rx={10} fill="var(--surface)" stroke="#10b981" strokeWidth={3} />
            <rect x={X_LEFT} y={Y_REVENUES} width={W_NODE} height={36} rx={10} fill="#10b981" />
            <text x={X_LEFT + W_NODE / 2} y={Y_REVENUES + 24} fill="#ffffff" fontSize="16" fontWeight="800" textAnchor="middle">
              REVENUES
            </text>
            <text x={X_LEFT + 20} y={Y_REVENUES + 70} fill="var(--ink)" fontSize="19" fontWeight="800">
              {nf(ordinaryRevenues, 1)} % PIB
            </text>
          </g>

          {/* --- RIGHT COLUMN BOXES --- */}
          {/* Box 1: DEBT (End of Year) */}
          <g onMouseEnter={() => setHoveredNode("debt")} onMouseLeave={() => setHoveredNode(null)}>
            <rect x={X_RIGHT} y={Y_DEBT_END} width={W_NODE} height={H_DEBT_END} rx={10} fill="var(--surface)" stroke="#8b5cf6" strokeWidth={3} />
            <rect x={X_RIGHT} y={Y_DEBT_END} width={W_NODE} height={36} rx={10} fill="#8b5cf6" />
            <text x={X_RIGHT + W_NODE / 2} y={Y_DEBT_END + 24} fill="#ffffff" fontSize="16" fontWeight="800" textAnchor="middle">
              DEBT (FINAL DE AÑO)
            </text>
            <text x={X_RIGHT + 20} y={Y_DEBT_END + 70} fill="var(--ink)" fontSize="18" fontWeight="800">
              {nf(b, 1)} % PIB
            </text>
            <text x={X_RIGHT + 20} y={Y_DEBT_END + 94} fill="var(--muted)" fontSize="13" fontWeight="600">
              Stock de Deuda Viva al final del ejercicio
            </text>
          </g>

          {/* Box 2: EXPENSES (Encompassing Deficit + Itemized Text Removed) */}
          <g onMouseEnter={() => setHoveredNode("rev")} onMouseLeave={() => setHoveredNode(null)}>
            <rect
              x={X_RIGHT}
              y={Y_EXPENSES}
              width={W_NODE}
              height={H_TOTAL_EXPENSES}
              rx={10}
              fill="var(--surface)"
              stroke="#0284c7"
              strokeWidth={3}
            />
            <rect x={X_RIGHT} y={Y_EXPENSES} width={W_NODE} height={36} rx={10} fill="#0284c7" />
            <text x={X_RIGHT + W_NODE / 2} y={Y_EXPENSES + 24} fill="#ffffff" fontSize="16" fontWeight="800" textAnchor="middle">
              EXPENSES
            </text>
            <text x={X_RIGHT + 20} y={Y_EXPENSES + 70} fill="var(--ink)" fontSize="19" fontWeight="800">
              {nf(ordinaryRevenues, 1)} % + {nf(Math.abs(deltaB), 1)} % PIB
            </text>

            {/* Inner Dotted Compartment encompassing the Deficit Fraction */}
            {isDeficit ? (
              <g>
                <rect
                  x={X_RIGHT + 4}
                  y={Y_DEFICIT_COMPARTMENT}
                  width={W_NODE - 8}
                  height={H_DEFICIT_COMPARTMENT - 4}
                  rx={6}
                  fill="rgba(239, 68, 68, 0.08)"
                  stroke="#ef4444"
                  strokeWidth={2}
                  strokeDasharray="5 3"
                />
                <text x={X_RIGHT + W_NODE / 2} y={Y_DEFICIT_COMPARTMENT + H_DEFICIT_COMPARTMENT / 2 + 5} fill="#ef4444" fontSize="13.5" fontWeight="800" textAnchor="middle">
                  Déficit Presupuestario (+{nf(deltaB, 1)} % PIB)
                </text>
              </g>
            ) : null}
          </g>

          {/* --- INTERNAL DOTTED ARROW & BADGE --- */}
          {isDeficit ? (
            <g>
              <path
                d={`M ${X_RIGHT} ${Y_DEFICIT_COMPARTMENT + H_DEFICIT_COMPARTMENT / 2} C ${X_RIGHT - 120} ${Y_DEFICIT_COMPARTMENT + H_DEFICIT_COMPARTMENT / 2}, ${X_RIGHT - 120} ${Y_DEBT_END + H_DEBT_END - 25}, ${X_RIGHT - 8} ${Y_DEBT_END + H_DEBT_END - 25}`}
                fill="none"
                stroke="#ef4444"
                strokeWidth="3.5"
                strokeDasharray="6 3"
                markerEnd="url(#arrow-red)"
              />

              <g transform={`translate(${X_RIGHT - 125}, ${(Y_DEFICIT_COMPARTMENT + H_DEFICIT_COMPARTMENT / 2 + Y_DEBT_END + H_DEBT_END - 25) / 2})`}>
                <rect x="-48" y="-22" width="96" height="42" rx="6" fill="var(--surface)" stroke="#ef4444" strokeWidth="1.5" />
                <text x="0" y="-4" fill="#ef4444" fontSize="13" fontWeight="900" textAnchor="middle">
                  NEW DEBT
                </text>
                <text x="0" y="13" fill="#ef4444" fontSize="12.5" fontWeight="800" textAnchor="middle">
                  +{nf(deltaB, 1)} % PIB
                </text>
              </g>
            </g>
          ) : isSuperavit ? (
            <g>
              <path
                d={`M ${X_RIGHT - 8} ${Y_DEBT_END + H_DEBT_END - 25} C ${X_RIGHT - 120} ${Y_DEBT_END + H_DEBT_END - 25}, ${X_RIGHT - 120} ${Y_DEFICIT_COMPARTMENT + H_DEFICIT_COMPARTMENT / 2}, ${X_RIGHT} ${Y_DEFICIT_COMPARTMENT + H_DEFICIT_COMPARTMENT / 2}`}
                fill="none"
                stroke="#10b981"
                strokeWidth="3.5"
                strokeDasharray="6 3"
                markerEnd="url(#arrow-green)"
              />

              <g transform={`translate(${X_RIGHT - 125}, ${(Y_DEFICIT_COMPARTMENT + H_DEFICIT_COMPARTMENT / 2 + Y_DEBT_END + H_DEBT_END - 25) / 2})`}>
                <rect x="-56" y="-22" width="112" height="42" rx="6" fill="var(--surface)" stroke="#10b981" strokeWidth="1.5" />
                <text x="0" y="-4" fill="#10b981" fontSize="12" fontWeight="900" textAnchor="middle">
                  AMORTISATION
                </text>
                <text x="0" y="13" fill="#10b981" fontSize="12.5" fontWeight="800" textAnchor="middle">
                  -{nf(-deltaB, 1)} % PIB
                </text>
              </g>
            </g>
          ) : null}
        </svg>
      </div>

      {/* --- Footer Summary --- */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 12, fontSize: 13, borderTop: "1px dashed var(--grid)", paddingTop: 12, marginTop: 10 }}>
        <div><b>Deuda al Inicio:</b> <span style={{ color: "var(--accent)", fontWeight: 800 }}>{nf(bPrev, 1)} % PIB</span></div>
        <div><b>Deuda al Final:</b> <span style={{ color: "var(--accent)", fontWeight: 800 }}>{nf(b, 1)} % PIB</span></div>
        <div><b>Variación Anual ($\Delta b$):</b> <span style={{ color: deltaB > 0 ? "var(--div-neg)" : "var(--good)", fontWeight: 800 }}>{deltaB >= 0 ? `+${nf(deltaB, 1)}` : nf(deltaB, 1)} % PIB</span></div>
        <div><b>Gastos Totales:</b> <span style={{ color: "var(--ink)", fontWeight: 800 }}>{nf(ordinaryRevenues, 1)} % + {nf(Math.abs(deltaB), 1)} % PIB</span></div>
      </div>
    </div>
  );
}
