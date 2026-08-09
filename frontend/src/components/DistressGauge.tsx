import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { nf } from "../lib/fmt";
import { Caption } from "../components/Caption";

/** Where a probability sits against the historical base rate.
 *
 *  Drawn on a log scale, because the interesting range spans two orders of
 *  magnitude: Spain is near 2 % and Argentina near 56 %, and a linear bar puts
 *  both of them and the base rate in the leftmost fifth.
 */
function scale(p: number): number {
  const lo = Math.log10(0.002), hi = Math.log10(1);
  return Math.max(0, Math.min(100, ((Math.log10(Math.max(p, 0.002)) - lo) / (hi - lo)) * 100));
}

export function DistressGauge() {
  const q = useQuery({ queryKey: ["distress"], queryFn: api.distress, staleTime: Infinity });

  if (q.isError) return null;
  if (!q.data?.available || !q.data.spain) {
    return q.data && !q.data.available
      ? <div className="banner">{q.data.note}</div>
      : null;
  }

  const d = q.data;
  const s = d.spain!;              // narrowed above; TS loses it across the guard
  const ratio = s.probability / d.base_rate;

  return (
    <div className="card">
      <h4>
        Probabilidad de entrar en impago
        <small>clasificador sobre {nf(d.n_positive, 0)} impagos reales, {d.years[0]}–{d.years[1]}</small>
      </h4>

      <div className="dg-head">
        <span className="dg-val">{nf(s.probability * 100, 2)} %</span>
        <span className="dg-ref">
          frente a {nf(d.base_rate * 100, 1)} % de tasa base ·{" "}
          <strong>{nf(1 / ratio, 0)}× por debajo</strong>
        </span>
      </div>

      <div className="dg-bar">
        <span className="dg-fill" style={{ width: `${scale(s.probability)}%` }} />
        <span className="dg-base" style={{ left: `${scale(d.base_rate)}%` }}
              title={`tasa base ${nf(d.base_rate * 100, 1)} %`} />
      </div>
      <div className="dg-axis">
        <span>0,2 %</span>
        {/* Anchored to the marker's own position, not centred: a label that
            points 12 points away from its line reads as a second data point. */}
        <span className="dg-axis-base" style={{ left: `${scale(d.base_rate)}%` }}>
          tasa base
        </span>
        <span>100 %</span>
      </div>

      <Caption>
        Es el complemento probabilístico del umbral del 7 % en el bono: el
        rendimiento dice lo que exige el mercado hoy, y esto a qué se parecieron
        los países que acabaron impagando. España ({s.year}) no está en la base
        de impagos — no ha impagado en el periodo — así que el modelo la puntúa
        sin haberla visto nunca.
      </Caption>
      <p className="src" style={{ whiteSpace: "normal" }}>
        AUC {nf(d.auc, 3)} ± {nf(d.auc_std, 3)} agrupada por país; PR-AUC{" "}
        {nf(d.pr_auc, 3)} frente a {nf(d.base_rate, 3)} sin modelo ({nf(d.pr_auc_lift, 1)}×).
        Es una capacidad discriminante modesta y se publica como tal: ordena
        razonablemente pero no calibra un nivel. Lee la posición relativa, no la
        cifra absoluta.
      </p>
    </div>
  );
}
