import {
  Area, CartesianGrid, ComposedChart, Line, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { nf } from "../lib/fmt";
import { useReducedMotion } from "../lib/motion";
import type { IrfOut } from "../api/types";

/** Estimated impulse response against the decay the engine assumes.
 *
 *  The two curves answer the same question — how long does a house-price shock
 *  last — from different sources, so they belong on one axis. Reporting the
 *  estimate alone would leave the reader to do the comparison by memory.
 */
export function IrfChart({ irf, height = 260 }: { irf: IrfOut; height?: number }) {
  const reduced = useReducedMotion();
  const engineAt = new Map(irf.engine_path.map((p) => [p.h, p.coef]));
  const data = irf.horizons.map((p) => ({
    years: p.years,
    band: [p.ci_low, p.ci_high] as [number, number],
    coef: p.coef,
    // null leaves a gap rather than drawing a line to zero: before the anchor
    // the engine's annual rule simply makes no claim.
    motor: engineAt.get(p.h) ?? null,
  }));
  const anchorYears = irf.anchor_h / 4;

  return (
    <div>
      <div className="legend">
        <span><i style={{ background: "var(--band-out)", height: 8 }} />banda 90 %</span>
        <span><i style={{ background: "var(--s1)" }} />estimado en el panel</span>
        <span><i style={{ background: "var(--s2)" }} />supuesto del motor</span>
      </div>
      <ResponsiveContainer width="100%" height={height} initialDimension={{ width: 660, height }}>
        <ComposedChart data={data} margin={{ top: 12, right: 12, bottom: 4, left: 0 }}>
          <CartesianGrid stroke="var(--grid)" vertical={false} />
          <XAxis dataKey="years" type="number" domain={[0, "dataMax"]}
            ticks={[0, 1, 2, 3]}
            tickFormatter={(v: number) => `${nf(v, 0)} a`}
            tick={{ fontSize: 13.5, fill: "var(--ink-2)" }}
            tickLine={false} axisLine={{ stroke: "var(--grid)" }} />
          <YAxis width={64} tick={{ fontSize: 13.5, fill: "var(--ink-2)" }} tickLine={false}
            axisLine={false} tickFormatter={(v: number) => nf(v, 2)} domain={["auto", "auto"]} />
          <ReferenceLine y={0} stroke="var(--grid)" />
          <ReferenceLine x={anchorYears} stroke="var(--grid)" strokeDasharray="2 3"
            label={{ value: "ancla", fontSize: 13.5, fill: "var(--ink-2)", position: "top" }} />
          <Tooltip
            formatter={(v, name) =>
              Array.isArray(v) ? `${nf(Number(v[0]), 2)} … ${nf(Number(v[1]), 2)}`
                : [nf(Number(v), 2), String(name)]}
            labelFormatter={(y) => `${nf(Number(y), 2)} años tras el choque`} />
          <Area dataKey="band" fill="var(--band-out)" fillOpacity={0.75} stroke="none"
            isAnimationActive={!reduced} animationDuration={200} />
          <Line dataKey="coef" name="estimado" stroke="var(--s1)" strokeWidth={2} dot={false}
            isAnimationActive={!reduced} animationDuration={200} />
          <Line dataKey="motor" name="motor" stroke="var(--s2)" strokeWidth={2}
            strokeDasharray="4 3" dot={false} connectNulls={false}
            isAnimationActive={!reduced} animationDuration={200} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
