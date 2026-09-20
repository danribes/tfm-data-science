import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { nf } from "../lib/fmt";
import { Caption } from "../components/Caption";

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

  return (
    <div className="card">
      <h4>
        Puntuación exploratoria de distress
        <small>clasificador sobre {nf(d.n_positive, 0)} impagos reales, {d.years[0]}–{d.years[1]}</small>
      </h4>

      <div className="dg-head">
        <span className="dg-val">{nf(s.probability, 4)}</span>
        <span className="dg-ref">
          escala 0–1 · <strong>sin calibración para España</strong>
        </span>
      </div>

      <div className="dg-bar">
        <span className="dg-fill" style={{ width: `${Math.max(0, Math.min(1, s.probability)) * 100}%` }} />
      </div>
      <div className="dg-axis">
        <span>0</span><span>1</span>
      </div>

      <Caption>
        Es una salida del clasificador, no una probabilidad de impago calibrada.
        España ({s.year}) no está en el conjunto etiquetado; su cobertura es de{" "}
        {s.coverage} variables. Esa exclusión evita entrenar con etiquetas españolas,
        pero no demuestra que el modelo se transfiera a España. No permite calcular
        un riesgo relativo frente a la tasa de eventos del panel.
      </Caption>
      <p className="src" style={{ whiteSpace: "normal" }}>
        AUC {nf(d.auc, 3)}; desviación entre particiones {nf(d.auc_std, 3)}.
        Validación agrupada por país, sin separación temporal. PR-AUC media{" "}
        {nf(d.pr_auc, 3)}; frecuencia de eventos en el panel {nf(d.base_rate * 100, 1)} %.
        Estas métricas describen discriminación en el panel histórico; no validan
        probabilidades absolutas ni comparaciones de riesgo para España.
      </p>
    </div>
  );
}
