import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { nf } from "../lib/fmt";

/** The library's report card, shown inside the library.
 *
 *  A chat that claims to answer only from its corpus is making a measurable
 *  promise, and a reader deciding whether to trust an answer deserves the
 *  measurements where the answers happen — not in a JSON three directories
 *  away. Every figure comes from the committed evaluation artifacts.
 */
export function RagReportCard() {
  const q = useQuery({ queryKey: ["rag", "eval"], queryFn: api.ragEval, staleTime: Infinity });

  if (!q.data?.available) return null;
  const d = q.data;

  const items: [string, string, boolean][] = [
    [`${nf(d.hit_rate * 100, 0)} %`,
     `el documento correcto aparece (top-8, ${nf(d.n_questions, 0)} preguntas doradas)`,
     d.hit_rate >= 0.9],
    [`${nf(d.unanswerable_refused, 0)}/${nf(d.unanswerable_total, 0)}`,
     "preguntas incontestables rechazadas en vez de inventadas",
     d.unanswerable_refused === d.unanswerable_total],
    [`${nf(d.cited_share * 100, 0)} %`,
     `frases con cita en las respuestas (${nf(d.dangling_answers, 0)} citas colgantes)`,
     d.cited_share >= 0.8 && d.dangling_answers === 0],
    [`${nf(d.fidelity_supported, 0)}/${nf(d.fidelity_checked, 0)}`,
     "frases citadas respaldadas por su pasaje (juez cruzado)",
     d.fidelity_supported >= d.fidelity_checked - 2],
  ];

  return (
    <div className="card rag-report">
      <h4>
        Esta biblioteca se evalúa
        <small>
          recuperación y chat, sobre preguntas escritas antes de mirar ·
          aislamiento de colecciones {d.isolation_clean ? "sin fugas" : "CON FUGAS"} ·
          guardarraíl de consejo {d.guardrail_clean ? "íntegro" : "ROTO"}
        </small>
      </h4>
      <div className="rag-report-row">
        {items.map(([value, label, ok]) => (
          <div key={label} className={ok ? "rr-item" : "rr-item bad"}>
            <span className="rr-val">{value}</span>
            <span className="rr-lab">{label}</span>
          </div>
        ))}
      </div>
      <p className="src" style={{ whiteSpace: "normal" }}>
        MRR {nf(d.mrr, 2)} · primera posición {nf(d.top1 * 100, 0)} %. Los números
        se regeneran con <code>python -m rag.evaluate</code> y{" "}
        <code>python -m rag.eval_chat</code>; el conjunto dorado y sus trampas
        viven en <code>rag/golden.py</code>. Una biblioteca sin evaluación es
        indistinguible de una que funciona — hasta la primera pregunta en público.
      </p>
    </div>
  );
}
