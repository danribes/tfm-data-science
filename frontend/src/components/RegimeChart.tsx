import { useQuery } from "@tanstack/react-query";
import {
  CartesianGrid, ComposedChart, Line, ReferenceArea, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { api } from "../api/client";
import { nf } from "../lib/fmt";
import { useReducedMotion } from "../lib/motion";
import { Caption } from "../components/Caption";

/** A century and a half of fiscal balance, with the crises found by a model.
 *
 *  The shading is detected, not annotated: a two-state hidden Markov model
 *  fitted to the balance itself, with no dates given to it. That it recovers
 *  the Sexenio, the World-War-I years, the post-Civil-War collapse and
 *  2008-2023 on its own is the argument the card makes — history sorts into
 *  calm and crisis, and the app's red lines are anchored in the second.
 */
export function RegimeChart() {
  const q = useQuery({ queryKey: ["regimes"], queryFn: api.regimes, staleTime: Infinity });
  const reduced = useReducedMotion();

  if (q.isError) return null;
  if (q.data && !q.data.available) return <div className="banner">{q.data.note}</div>;
  const f = q.data?.fiscal;
  if (!f) return null;

  const data = f.periods.map((p, i) => ({
    year: Number(p),
    bal: f.values[i],
    p: f.p_crisis[i],
  }));

  return (
    <div className="card">
      <h4>
        Siglo y medio de calma y crisis
        <small>
          saldo público español {String(f.periods[0])}–{String(f.periods[f.periods.length - 1])} ·
          regímenes detectados, no anotados a mano
        </small>
      </h4>
      <div className="legend">
        <span><i style={{ background: "var(--s1)" }} />saldo (ingresos − gastos), % PIB</span>
        <span><i style={{ background: "var(--st-crossed-bg)", height: 10 }} />régimen de crisis (HMM)</span>
      </div>
      <ResponsiveContainer width="100%" height={280} initialDimension={{ width: 660, height: 280 }}>
        <ComposedChart data={data} margin={{ top: 12, right: 12, bottom: 4, left: 0 }}>
          <CartesianGrid stroke="var(--grid)" vertical={false} />
          {f.episodes.map((e) => (
            <ReferenceArea key={`${e.from}`} x1={Number(e.from)} x2={Number(e.to)}
              fill="var(--st-crossed-bg)" fillOpacity={0.55} stroke="none" />
          ))}
          <XAxis dataKey="year" type="number" domain={["dataMin", "dataMax"]}
            ticks={[1850, 1875, 1900, 1925, 1950, 1975, 2000, 2025]}
            tick={{ fontSize: 12.5, fill: "var(--ink-2)" }} tickLine={false}
            axisLine={{ stroke: "var(--grid)" }} />
          <YAxis width={52} tick={{ fontSize: 12.5, fill: "var(--ink-2)" }} tickLine={false}
            axisLine={false} tickFormatter={(v: number) => nf(v, 0)} />
          <ReferenceLine y={0} stroke="var(--ink-2)" strokeWidth={1} />
          <Tooltip
            formatter={(v, name) => name === "p"
              ? [nf(Number(v) * 100, 0) + " %", "prob. de crisis"]
              : [nf(Number(v), 1) + " % PIB", "saldo"]}
            labelFormatter={(y) => `año ${y}`} />
          <Line dataKey="bal" name="bal" stroke="var(--s1)" strokeWidth={1.8} dot={false}
            isAnimationActive={!reduced} animationDuration={200} />
          <Line dataKey="p" hide dot={false} isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
      <Caption>
        Las bandas no vienen de un libro de historia: un modelo oculto de Márkov
        de dos estados, ajustado sólo al saldo, separa por su cuenta el Sexenio,
        los años de la Gran Guerra, la posguerra civil y 2008–2023. Los años
        1936–39 no aparecen porque el Estado no publicó cuentas — el hueco es
        del dato, no del modelo. La lección para el resto de la app: el saldo
        español no oscila alrededor de una media, alterna entre dos mundos, y
        las líneas rojas están ancladas en el malo.
      </Caption>
      <p className="src" style={{ whiteSpace: "normal" }}>
        {q.data?.method} · serie gold_fiscal_historico.csv · reproducible con
        <code> python -m research.regimes</code>
      </p>
    </div>
  );
}
