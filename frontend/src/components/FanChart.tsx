import {
  Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { nf } from "../lib/fmt";
import { useReducedMotion } from "../lib/motion";
import type { PercentileKey } from "../api/types";

export function FanChart({ years, percentiles, height = 260 }: {
  years: number[]; percentiles: Record<PercentileKey, number[]>; height?: number;
}) {
  const reduced = useReducedMotion();
  const data = years.map((y, i) => ({
    year: y,
    band95: [percentiles.p5[i], percentiles.p95[i]],
    band50: [percentiles.p25[i], percentiles.p75[i]],
    p50: percentiles.p50[i],
  }));
  return (
    <div>
      <div className="legend">
        <span><i style={{ background: "var(--band-out)", height: 8 }} />banda p5–p95</span>
        <span><i style={{ background: "var(--band-in)", height: 8 }} />banda p25–p75</span>
        <span><i style={{ background: "var(--s1)" }} />mediana p50</span>
      </div>
      <ResponsiveContainer width="100%" height={height} initialDimension={{ width: 660, height }}>
        <ComposedChart data={data} margin={{ top: 12, right: 12, bottom: 4, left: 0 }}>
          <CartesianGrid stroke="var(--grid)" vertical={false} />
          <XAxis dataKey="year" ticks={[years[0], 2050, years[years.length - 1]]}
            tick={{ fontSize: 13.5, fill: "var(--ink-2)" }} tickLine={false} axisLine={{ stroke: "var(--grid)" }} />
          <YAxis width={64} tick={{ fontSize: 13.5, fill: "var(--ink-2)" }} tickLine={false}
            axisLine={false} tickFormatter={(v: number) => nf(v, 0)} domain={["auto", "auto"]} />
          <Tooltip formatter={(v) =>
            Array.isArray(v) ? `${nf(Number(v[0]), 1)} – ${nf(Number(v[1]), 1)}` : nf(Number(v), 1)}
            labelFormatter={(y) => `año ${y}`} />
          <Area dataKey="band95" fill="var(--band-out)" fillOpacity={0.75} stroke="none"
            isAnimationActive={!reduced} animationDuration={200} />
          <Area dataKey="band50" fill="var(--band-in)" fillOpacity={0.8} stroke="none"
            isAnimationActive={!reduced} animationDuration={200} />
          <Line dataKey="p50" stroke="var(--s1)" strokeWidth={2} dot={false}
            isAnimationActive={!reduced} animationDuration={200} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
