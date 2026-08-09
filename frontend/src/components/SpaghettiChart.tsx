import {
  CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { nf } from "../lib/fmt";

/** Individual Monte Carlo debt trajectories — the "spaghetti".
 *
 *  A percentile fan is the honest summary of where the probability mass sits,
 *  but it reads as a smooth corridor and invites the eye to treat the median as
 *  a forecast. The individual paths break that illusion: each strand is one
 *  internally consistent future, and they visibly do not travel together. Some
 *  improve for a decade before turning; some never turn.
 *
 *  Drawn deliberately thin and translucent so the *density* is the message —
 *  where strands bunch, outcomes are likely; where they fan apart, the model is
 *  saying it cannot tell those futures apart. */
export function SpaghettiChart({
  years,
  paths,
  median,
  thresholds = [],
  height = 260,
}: {
  years: number[];
  paths: number[][];
  median?: number[];
  thresholds?: { value: number; label: string }[];
  height?: number;
}) {
  if (paths.length === 0 || years.length === 0) return null;

  // Recharts wants row-per-x, so pivot once: { year, p0, p1, …, med }.
  const data = years.map((year, i) => {
    const row: Record<string, number> = { year };
    paths.forEach((p, j) => {
      if (p[i] !== undefined) row[`p${j}`] = p[i];
    });
    if (median?.[i] !== undefined) row.med = median[i];
    return row;
  });

  return (
    <div className="spag">
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 6, right: 8, bottom: 2, left: 0 }}>
          <CartesianGrid stroke="var(--grid)" vertical={false} />
          <XAxis
            dataKey="year"
            tick={{ fontSize: 13.5, fill: "var(--muted)" }}
            tickLine={false}
            axisLine={{ stroke: "var(--grid)" }}
            interval="preserveStartEnd"
            minTickGap={40}
          />
          <YAxis
            tick={{ fontSize: 13.5, fill: "var(--muted)" }}
            tickLine={false}
            axisLine={false}
            width={56}
            tickFormatter={(v: number) => nf(v, 0)}
          />
          {thresholds.map((t) => (
            <ReferenceLine
              key={t.label}
              y={t.value}
              stroke="var(--st-crossed)"
              strokeDasharray="4 3"
              strokeWidth={1}
              label={{
                value: t.label,
                position: "insideTopLeft",
                fill: "var(--st-crossed)",
                fontSize: 13.5,
              }}
            />
          ))}
          {paths.map((_, j) => (
            <Line
              key={j}
              type="monotone"
              dataKey={`p${j}`}
              stroke="var(--accent)"
              strokeWidth={0.7}
              strokeOpacity={0.22}
              dot={false}
              isAnimationActive={false}
              tooltipType="none"
            />
          ))}
          {median && (
            <Line
              type="monotone"
              dataKey="med"
              stroke="var(--ink)"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          )}
          <Tooltip
            contentStyle={{
              background: "var(--card)",
              border: "1px solid var(--grid)",
              borderRadius: 6,
              fontSize: 13.5,
              padding: "8px 12px",
            }}
            labelFormatter={(y) => `año ${y}`}
            formatter={(v, name) => {
              if (name === "med") {
                return [`${nf(Number(v), 1)} %PIB`, "mediana Monte Carlo"];
              }
              return [undefined, undefined];
            }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
