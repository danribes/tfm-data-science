import { useEffect, useState } from "react";
import type { Levers } from "../engine/levers";
import { runScenario } from "../engine/spain";
import { nf } from "../lib/fmt";
import { debtRatioBridge } from "./fiscalFlows";

export function DebtAmortizationFlowChart({ levers, horizon = 2030 }: { levers: Levers; horizon?: number }) {
  const [selectedYear, setSelectedYear] = useState(horizon);
  useEffect(() => setSelectedYear(horizon), [horizon]);
  const scn = runScenario(levers);
  const k = Math.max(0, Math.min(24, selectedYear - 2026));
  const bridge = debtRatioBridge(scn, k);
  const signed = (v: number) => `${v >= 0 ? "+" : ""}${nf(v, 2)}`;
  if (!Object.values(bridge).every(Number.isFinite) || bridge.previous < 0 || bridge.current < 0
    || Math.abs(bridge.residual) > 1e-8) {
    return <div className="card" role="status">Descomposición de deuda no disponible fuera del dominio contable del escenario.</div>;
  }
  const columns = [
    { label: `Ratio al cierre de ${selectedYear - 1}`, value: nf(bridge.previous, 2), unit: "% del PIB del año anterior", color: "#8b5cf6" },
    { label: "Efecto del crecimiento nominal", value: signed(bridge.denominatorEffect), unit: "puntos porcentuales de ratio", color: "#0284c7" },
    { label: "Contribución del saldo fiscal", value: signed(bridge.fiscalContribution), unit: "déficit (+) / superávit (−)", color: "#f97316" },
    { label: `Ratio al cierre de ${selectedYear}`, value: nf(bridge.current, 2), unit: "% del PIB del año actual", color: "#8b5cf6" },
  ];
  return <div className="card" style={{ padding: 20, marginTop: 16 }}>
    <h4 style={{ marginTop: 0 }}>Deuda/PIB: saldo fiscal y efecto del crecimiento</h4>
    <p className="muted">Descomposición contable del escenario; cajas ilustrativas, sin escala de volumen. La variación de la ratio incorpora el cambio del denominador PIB.</p>
    <label htmlFor="flow-year-select">Año de proyección: </label>
    <select id="flow-year-select" value={selectedYear} onChange={(e) => setSelectedYear(Number(e.target.value))}>
      {[2026, 2030, 2035, 2040, 2045, 2050].map((y) => <option key={y} value={y}>{y}</option>)}
    </select>
    <div style={{ overflowX: "auto", marginTop: 16 }}>
      <svg role="img" aria-label={`Descomposición de la variación de deuda sobre PIB en ${selectedYear}`} viewBox="0 0 1000 170" style={{ width: "100%", minWidth: 700 }}>
        {columns.map((c, i) => <g key={c.label} transform={`translate(${i * 255}, 15)`}>
          <rect x={0} y={0} width={230} height={135} rx={8} fill="var(--surface)" stroke={c.color} strokeWidth={2} />
          <text x={115} y={30} textAnchor="middle" fill="var(--ink)" fontSize={13}>{c.label}</text>
          <text x={115} y={75} textAnchor="middle" fill={c.color} fontSize={27} fontWeight={800}>{c.value}</text>
          <text x={115} y={108} textAnchor="middle" fill="var(--muted)" fontSize={12}>{c.unit}</text>
          {i < 3 && <text x={242} y={77} textAnchor="middle" fill="var(--ink)" fontSize={24}>{i < 2 ? "+" : "="}</text>}
        </g>)}
      </svg>
    </div>
    <p><b>Variación de deuda/PIB:</b> {signed(bridge.change)} puntos porcentuales. <b>Saldo presupuestario:</b> {signed(scn.saldo[k])} % del PIB.</p>
    <p className="muted">Una caída de deuda/PIB puede coexistir con déficit. El modelo no desglosa emisiones brutas, vencimientos ni amortizaciones; tampoco incluye ajustes stock-flujo.</p>
  </div>;
}
