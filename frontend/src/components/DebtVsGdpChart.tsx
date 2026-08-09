import {
  Area, ComposedChart, CartesianGrid, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { nf, sg } from "../lib/fmt";
import type { Scenario } from "../engine/spain";

/** The rescue-zone threshold. Greece, Portugal and Ireland each requested a
 *  bailout with the 10-year yield around this level; Spain touched 7.6 % in
 *  July 2012. It is not a law of nature — it is where market access has
 *  historically closed. */
export const RESCUE_YIELD = 7.0;

export interface DebtVsGdpPoint {
  year: number;
  pib: number;
  deuda: number;
  ratio: number;
}

/** Compound the debt and the economy from the same starting point.
 *
 *  Both series are indexed to the first year = 100 rather than shown in euros.
 *  That is a deliberate limitation, not an oversight: the frozen vintage has no
 *  nominal euro GDP level (`gold_bienestar_pais.csv` carries GDP per capita in
 *  PPS, which is a different unit), and multiplying it out would produce an
 *  authoritative-looking euro figure the data does not support.
 *
 *  The index answers the question anyway, and arguably better. Debt compounds
 *  at roughly the effective interest rate; the economy compounds at the nominal
 *  growth rate. The ratio between the two curves *is* the debt-to-GDP ratio, so
 *  the widening gap is the repayment problem drawn directly. */
export function debtVsGdpSeries(scn: Scenario, years: number[]): DebtVsGdpPoint[] {
  const out: DebtVsGdpPoint[] = [];
  let pibIdx = 100;
  const b0 = scn.b[0];
  for (let i = 0; i < years.length; i++) {
    if (i > 0) pibIdx *= 1 + scn.gnom[i] / 100;
    // deuda(t)/deuda(0) = [b(t)·PIB(t)] / [b(0)·PIB(0)]
    const deudaIdx = b0 !== 0 ? (scn.b[i] / b0) * pibIdx : 0;
    out.push({ year: years[i], pib: pibIdx, deuda: deudaIdx, ratio: scn.b[i] });
  }
  return out;
}

export function DebtVsGdpChart({
  scn,
  years,
  height = 260,
}: {
  scn: Scenario;
  years: number[];
  height?: number;
}) {
  const data = debtVsGdpSeries(scn, years).map((p) => ({
    ...p,
    // The shaded band is the excess of debt over the economy — the part that
    // growth has not absorbed.
    exceso: Math.max(0, p.deuda - p.pib),
    base: Math.min(p.deuda, p.pib),
  }));

  const last = data[data.length - 1];
  const first = data[0];

  return (
    <div>
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={data} margin={{ top: 6, right: 8, bottom: 2, left: 0 }}>
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
          <Area
            type="monotone"
            dataKey="base"
            stackId="gap"
            stroke="none"
            fill="transparent"
            isAnimationActive={false}
            legendType="none"
          />
          <Area
            type="monotone"
            dataKey="exceso"
            stackId="gap"
            stroke="none"
            fill="var(--st-crossed)"
            fillOpacity={0.14}
            isAnimationActive={false}
            name="Deuda que el crecimiento no absorbe"
          />
          <Line
            type="monotone"
            dataKey="pib"
            stroke="var(--good)"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
            name="PIB nominal (índice)"
          />
          <Line
            type="monotone"
            dataKey="deuda"
            stroke="var(--st-crossed)"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
            name="Deuda total (índice)"
          />
          <Legend wrapperStyle={{ fontSize: 13.5 }} iconSize={12} />
          <Tooltip
            contentStyle={{
              background: "var(--card)",
              border: "1px solid var(--grid)",
              borderRadius: 6,
              fontSize: 13.5,
            }}
            labelFormatter={(y) => `año ${y}`}
            formatter={(v, name) => [nf(Number(v), 0), String(name)]}
          />
        </ComposedChart>
      </ResponsiveContainer>

      <p className="dvg-read">
        Partiendo ambos de 100 en {first.year}: en {last.year} la economía está en{" "}
        <strong>{nf(last.pib, 0)}</strong> y la deuda en{" "}
        <strong>{nf(last.deuda, 0)}</strong>. La deuda se multiplica por{" "}
        {nf(last.deuda / 100, 1)} y el PIB por {nf(last.pib / 100, 1)}; por eso la
        ratio pasa de {nf(first.ratio, 1)} a {nf(last.ratio, 1)} %PIB
        ({sg(last.ratio - first.ratio, 1)}).
      </p>
    </div>
  );
}

/** Where the 10-year yield sits against the rescue zone, and whether the
 *  snowball is running (effective rate above nominal growth). */
export function SnowballStrip({ scn, k }: { scn: Scenario; k: number }) {
  const bono = scn.bono[k];
  const r = scn.ief[k];
  const g = scn.gnom[k];
  const diff = r - g;
  const snowball = diff > 0;
  const pct = Math.min(100, Math.max(0, (bono / (RESCUE_YIELD * 1.3)) * 100));

  return (
    <div className="snow">
      <div className="snow-row">
        <span className="snow-lab">Bono a 10 años</span>
        <span className="snow-track">
          <span className="snow-fill" style={{ width: `${pct}%` }} />
          <span
            className="snow-mark"
            style={{ left: `${(RESCUE_YIELD / (RESCUE_YIELD * 1.3)) * 100}%` }}
            title={`Zona de rescate: ${nf(RESCUE_YIELD, 0)} %`}
          />
        </span>
        <span className={bono >= RESCUE_YIELD ? "snow-val bad" : "snow-val"}>
          {nf(bono, 2)} %
        </span>
      </div>
      <div className="snow-row">
        <span className="snow-lab">Tipo efectivo − crecimiento (r − g)</span>
        <span className={snowball ? "snow-badge bad" : "snow-badge ok"}>
          {sg(diff, 2)} pp — {snowball ? "bola de nieve activa" : "el crecimiento diluye"}
        </span>
      </div>
    </div>
  );
}
