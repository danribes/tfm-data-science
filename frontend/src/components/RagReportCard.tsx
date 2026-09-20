import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { useRagConnection } from "../api/hooks";
import { nf } from "../lib/fmt";

/** The library's report card, shown inside the library.
 *
 *  A chat that claims to answer only from its corpus is making a measurable
 *  promise, and a reader deciding whether to trust an answer deserves the
 *  measurements where the answers happen — not in a JSON three directories
 *  away. Every figure comes from the committed evaluation artifacts.
 */
export function RagReportCard() {
  const connection = useRagConnection();
  const q = useQuery({
    queryKey: ["rag", connection.baseUrl, connection.revision, "eval"],
    queryFn: api.ragEval, staleTime: Infinity, retry: false, gcTime: 0,
  });

  if (!q.data) return null;
  const d = q.data;
  if (!d.available) return (
    <div className="card rag-report">
      <h4>Evaluación de la biblioteca conectada</h4>
      <p className="layer-note">{d.note || "No hay resultados de evaluación disponibles para esta biblioteca."}</p>
    </div>
  );

  const items: [string, string][] = [
    [`${nf(d.hit_rate * 100, 0)} %`,
     `documento esperado en top-8 (${nf(d.n_questions, 0)} preguntas de desarrollo)`],
    [`${nf(d.unanswerable_refused, 0)}/${nf(d.unanswerable_total, 0)}`,
     "preguntas sin respuesta en el corpus con abstención detectada"],
    [`${nf(d.cited_share * 100, 0)} %`,
     `frases con cita en las respuestas (${nf(d.dangling_answers, 0)} respuestas con referencias inválidas)`],
    [`${nf(d.fidelity_supported, 0)}/${nf(d.fidelity_checked, 0)}`,
     "primeras frases citadas que otro modelo considera respaldadas"],
  ];

  return (
    <div className="card rag-report">
      <h4>
        Evaluación de desarrollo del proyecto
        <small>
          evaluación preliminar sobre preguntas usadas para ajustar la recuperación ·
          aislamiento de colecciones {d.isolation_clean ? "sin fugas" : "CON FUGAS"} ·
          filtro de consejo {d.guardrail_clean ? "sin fallos en las sondas evaluadas" : "con fallos en las sondas evaluadas"}
        </small>
      </h4>
      <div className="rag-report-row">
        {items.map(([value, label]) => (
          <div key={label} className="rr-item">
            <span className="rr-val">{value}</span>
            <span className="rr-lab">{label}</span>
          </div>
        ))}
      </div>
      <p className="src" style={{ whiteSpace: "normal" }}>
        MRR {nf(d.mrr, 2)} · primera posición {nf(d.top1 * 100, 0)} %. Los números
        se regeneran con <code>python -m rag.evaluate</code> y{" "}
        <code>python -m rag.eval_chat</code>; el conjunto dorado y sus trampas
        viven en <code>rag/golden.py</code>. Son resultados de desarrollo, no de
        un test independiente, y no validan automáticamente otro servicio o corpus. Encontrar un documento o mostrar una cita no
        demuestra que toda la respuesta sea correcta. La revisión de fidelidad
        abarca una frase por respuesta y aún necesita validación humana.
      </p>
    </div>
  );
}
