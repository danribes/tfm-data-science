import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, ragChatStream } from "../api/client";
import type { Authority, Passage, RagChatResponse } from "../api/types";
import { useScenarioStore } from "../state/scenarioStore";
import { nf } from "../lib/fmt";

/** How much weight a source carries, shown rather than assumed.
 *  A textbook and a YouTube transcript both produce text; only one of them is
 *  evidence, and the reader is entitled to see which is which. */
const AUTHORITY_LABEL: Record<Authority, string> = {
  academico: "manual / fuente académica",
  propio: "documentación de este modelo",
  opinion: "opinión — no es fuente académica",
};

function PassageCard({ p, index }: { p: Passage; index: number }) {
  const [open, setOpen] = useState(false);
  return (
    <li className={`psg ${p.authority}`}>
      <div className="psg-head">
        <span className="psg-n">[{index}]</span>
        <span className="psg-cite">{p.cita}</span>
        <span className={`psg-auth ${p.authority}`}>{AUTHORITY_LABEL[p.authority]}</span>
      </div>
      <p className={open ? "psg-text open" : "psg-text"}>{p.text}</p>
      <button type="button" className="psg-more" onClick={() => setOpen((v) => !v)}>
        {open ? "▾ menos" : "▸ ver el pasaje completo"}
      </button>
    </li>
  );
}

const EXAMPLES = [
  "¿por qué sube la deuda cuando el tipo de interés supera al crecimiento?",
  "¿cuánto vale el multiplicador fiscal en un país con deuda elevada?",
  "¿qué dice la literatura sobre el esfuerzo hipotecario de los hogares?",
  "¿qué son las proyecciones locales y para qué sirven?",
];

export default function Biblioteca() {
  const collections = useQuery({
    queryKey: ["rag", "collections"],
    queryFn: api.ragCollections,
    staleTime: Infinity,
  });

  const levers = useScenarioStore((s) => s.levers);
  const horizon = useScenarioStore((s) => s.horizon);

  const [question, setQuestion] = useState("");
  const [collection, setCollection] = useState("libros");
  const [withScenario, setWithScenario] = useState(false);
  const [answer, setAnswer] = useState<RagChatResponse | null>(null);
  const [passages, setPassages] = useState<Passage[]>([]);
  const [asked, setAsked] = useState("");

  const [streamed, setStreamed] = useState("");
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  // One streamed request rather than two round trips. The server emits the
  // passages as soon as retrieval finishes (~0,8 s) and then the answer word by
  // word, so time-to-first-content is under a second instead of the ~5,5 s it
  // took to wait for the whole generation.
  const submit = (q: string) => {
    const text = q.trim();
    if (text.length < 2 || busy) return;
    setQuestion(text);
    setAsked(text);
    setAnswer(null);
    setPassages([]);
    setStreamed("");
    setFailed(false);
    setBusy(true);

    ragChatStream(
      {
        question: text,
        collection,
        top_k: 8,
        include_scenario: withScenario,
        levers: withScenario ? levers : undefined,
        horizon: withScenario ? horizon : undefined,
      },
      {
        onPassages: (ps) => setPassages(ps),
        onDelta: (piece) => setStreamed((prev) => prev + piece),
        onDone: (final) =>
          setAnswer({
            vintage: "", computed_not_advice: true,
            question: text, collection,
            answer: final.answer, passages: [],
            grounded: final.grounded, provider: final.provider,
            model: final.model, error: final.error ?? null,
          } as RagChatResponse),
      },
    )
      .catch(() => setFailed(true))
      .finally(() => setBusy(false));
  };

  const shown = passages;
  // While streaming, render what has arrived; once done, the final text (they
  // agree, but `done` is authoritative if a provider died mid-stream).
  const answerText = answer?.answer ?? streamed;

  const active = collections.data?.collections.find((c) => c.id === collection);
  const empty = active && active.chunks === 0;

  return (
    <div className="biblio">
      <div className="head">
        <h1>Biblioteca</h1>
        <span className="meta">
          {collections.isSuccess
            ? `${nf(collections.data.total_documents, 0)} documentos · ${nf(collections.data.total_chunks, 0)} pasajes indexados`
            : "cargando el índice…"}
        </span>
      </div>

      <div className="card">
        <p className="biblio-intro">
          Pregunta sobre economía y te respondo <strong>sólo con lo que hay en el
          corpus</strong>, citando el pasaje. Si el corpus no cubre la pregunta,
          lo digo en vez de rellenar el hueco: una respuesta sin cita parece
          fundamentada y no lo está.
        </p>

        <div className="biblio-colls">
          {(collections.data?.collections ?? []).map((c) => (
            <button
              key={c.id}
              type="button"
              className={c.id === collection ? "coll on" : "coll"}
              onClick={() => setCollection(c.id)}
              title={c.note}
            >
              <span className="coll-label">{c.label}</span>
              <span className={`coll-auth ${c.authority}`}>{c.authority}</span>
              <span className="coll-n">{nf(c.chunks, 0)}</span>
            </button>
          ))}
        </div>
        {active && <p className="biblio-note">{active.note}</p>}
        {empty && (
          <div className="banner">
            Esta colección aún no está indexada. Ejecuta{" "}
            <code>python -m rag.ingest --collection {collection}</code>.
          </div>
        )}

        <form
          className="biblio-form"
          onSubmit={(e) => {
            e.preventDefault();
            submit(question);
          }}
        >
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="¿por qué sube la deuda cuando el tipo supera al crecimiento?"
            aria-label="Pregunta"
          />
          <button type="submit" disabled={busy || question.trim().length < 2}>
            {busy ? "buscando…" : "preguntar"}
          </button>
        </form>

        <label className="biblio-scn">
          <input
            type="checkbox"
            checked={withScenario}
            onChange={(e) => setWithScenario(e.target.checked)}
          />
          Enviar también el escenario que tengo puesto — la respuesta podrá
          enlazar la teoría citada con los números que hay ahora en pantalla.
        </label>

        <div className="biblio-eg">
          {EXAMPLES.map((q) => (
            <button key={q} type="button" onClick={() => submit(q)}>
              {q}
            </button>
          ))}
        </div>
      </div>

      {failed && (
        <div className="banner err">
          No se pudo consultar la biblioteca. ¿Está el índice construido y la API
          en marcha?
        </div>
      )}

      {(asked || answer) && (
        <div className="card">
          <h4>
            Respuesta
            {answer && !answer.grounded && <small>sin pasajes — el corpus no lo cubre</small>}
          </h4>

          {answerText ? (
            <p className="biblio-answer" aria-live="polite">
              {answerText}
              {busy && <span className="biblio-caret" aria-hidden="true" />}
            </p>
          ) : (
            <p className="biblio-pending" aria-live="polite">
              <span className="biblio-dots" aria-hidden="true" />
              {shown.length
                ? "Redactando la respuesta. Los pasajes de abajo ya son los que va a usar — puedes ir leyéndolos."
                : "Buscando en el corpus…"}
            </p>
          )}

          {shown.length > 0 && (
            <>
              <h4 className="biblio-src">
                {answer ? "Pasajes citados" : "Pasajes recuperados"}{" "}
                <small>{shown.length}</small>
              </h4>
              <ol className="psg-list">
                {shown.map((p, i) => (
                  <PassageCard key={p.chunk_id} p={p} index={i + 1} />
                ))}
              </ol>
            </>
          )}

          {answer && (
            <p className="biblio-prov">
              {answer.provider ? (
                <>
                  Redactado por <code>{answer.model}</code> a partir de los
                  pasajes de arriba. El modelo elige las palabras; las fuentes
                  son las citadas.
                </>
              ) : (
                <>
                  Sin proveedor de lenguaje disponible
                  {answer.error ? ` (${answer.error})` : ""} — se muestran los
                  pasajes recuperados sin redactar.
                </>
              )}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
