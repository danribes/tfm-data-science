import {
  CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { nf } from "../lib/fmt";
import { useReducedMotion } from "../lib/motion";

export function ProjectionChart({ years, baseline, scenario, redLines = [], unit = "", dec = 1, height = 260 }: {
  years: number[]; baseline: number[]; scenario: number[];
  redLines?: { value: number; label: string }[]; unit?: string; dec?: number; height?: number;
}) {
  const reduced = useReducedMotion();
  const data = years.map((y, i) => ({ year: y, base: baseline[i], esc: scenario[i] }));
  return (
    <div>
      <div className="legend">
        <span><i style={{ background: "var(--lab)" }} />escenario actual</span>
        <span><s />base congelada (vintage)</span>
        {redLines.length > 0 && <span><s style={{ borderColor: "var(--div-neg)" }} />línea roja</span>}
      </div>
      <ResponsiveContainer width="100%" height={height} initialDimension={{ width: 660, height }}>
        <LineChart data={data} margin={{ top: 12, right: 12, bottom: 4, left: 0 }}>
          <CartesianGrid stroke="var(--grid)" vertical={false} />
          <XAxis dataKey="year" ticks={[years[0], years[Math.floor((years.length - 1) / 2)], years[years.length - 1]]}
            tick={{ fontSize: 9.5, fill: "var(--ink-2)" }} tickLine={false} axisLine={{ stroke: "var(--grid)" }} />
          <YAxis width={56} tick={{ fontSize: 9.5, fill: "var(--ink-2)" }} tickLine={false}
            axisLine={false} tickFormatter={(v: number) => nf(v, dec)}
            domain={["auto", "auto"]} />
          <Tooltip formatter={(v) => `${nf(Number(v), dec)} ${unit}`} labelFormatter={(y) => `año ${y}`} />
          {redLines.map((rl) => (
            <ReferenceLine key={rl.label} y={rl.value} stroke="var(--div-neg)" strokeDasharray="4 3"
              label={{ value: rl.label, fontSize: 9, fill: "var(--div-neg)", position: "insideTopRight" }} />
          ))}
          <Line type="linear" dataKey="base" stroke="var(--baseline)" strokeWidth={1.6}
            strokeDasharray="5 4" dot={false} isAnimationActive={false} name="base" />
          <Line type="linear" dataKey="esc" stroke="var(--lab)" strokeWidth={2.4} dot={false}
            isAnimationActive={!reduced} animationDuration={200} name="escenario" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
