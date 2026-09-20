import { useState, useRef, useEffect } from "react";
import { ragChatStream } from "../api/client";
import { selectRagCollection, useRagCollections, useRagConnection } from "../api/hooks";
import { RagConnectionSettings } from "../components/RagConnectionSettings";
import { PUBLIC_RAG_EXAMPLES, RagCorpusNotice } from "../components/RagCorpusNotice";
import type { Passage, RagChatResponse } from "../api/types";

type Failure = { status?: number; detail: string };

function toFailure(e: unknown): Failure {
  const err = e as { status?: number; detail?: string; message?: string } | null;
  return { status: err?.status, detail: err?.detail ?? err?.message ?? String(e) };
}

const AUTHORITY_LABEL: Record<string, string> = {
  academico: "fuente académica",
  propio: "documentación del modelo",
  opinion: "opinión",
};

const EXAMPLES = [
  "¿Por qué sube la deuda pública cuando el tipo de interés supera al crecimiento?",
  "¿Qué es la curva de Phillips y qué dice sobre inflación y desempleo?",
  "¿Cómo afecta la política fiscal al crecimiento en una economía con deuda elevada?",
  "¿Qué son las expectativas racionales y en qué se diferencian de las adaptativas?",
];

export default function Consulta() {
  const [question, setQuestion] = useState("");
  const [asked, setAsked] = useState("");
  const [streamed, setStreamed] = useState("");
  const [passages, setPassages] = useState<Passage[]>([]);
  const [answer, setAnswer] = useState<RagChatResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<Failure | null>(null);
  const answerRef = useRef<HTMLDivElement>(null);

  const connection = useRagConnection();
  const collections = useRagCollections();
  const isPublic = collections.data?.corpus_scope === "public_project_docs";
  const collection = selectRagCollection(collections.data?.collections, collections.data?.default_collection);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => {
    setAsked(""); setStreamed(""); setPassages([]); setAnswer(null); setFailure(null); setBusy(false);
    return () => controller.current?.abort();
  }, [connection.revision]);
  const collectionFailure = collections.isError ? toFailure(collections.error) : null;

  const answerText = answer?.answer ?? streamed;

  useEffect(() => {
    if (streamed && answerRef.current) {
      answerRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [streamed]);

  const submit = (q: string) => {
    const text = q.trim();
    if (text.length < 2 || busy || !collection) return;
    setAsked(text);
    setQuestion("");
    setAnswer(null);
    setPassages([]);
    setStreamed("");
    setFailure(null);
    setBusy(true);

    const request = new AbortController();
    controller.current = request;
    ragChatStream(
      { question: text, collection: collection.id, top_k: 6 },
      {
        onPassages: (ps) => setPassages(ps),
        onDelta: (piece) => setStreamed((prev) => prev + piece),
        onDone: (final) =>
          setAnswer({
            vintage: "", computed_not_advice: true,
            question: text, collection: collection.id,
            answer: final.answer, passages: [],
            grounded: final.grounded, provider: final.provider,
            model: final.model, error: final.error ?? null,
          } as RagChatResponse),
      },
      request.signal,
    )
      .catch((e: unknown) => { if (!request.signal.aborted) setFailure(toFailure(e)); })
      .finally(() => { if (!request.signal.aborted) setBusy(false); });
  };

  const displayedFailure = failure ?? collectionFailure;

  return (
    <div className="consulta">
      <div className="head">
        <h1>Consulta económica</h1>
        <span className="meta">
          {isPublic
            ? "Consulta la documentación del proyecto — con cita o sin respuesta."
            : "Respondo con los textos del corpus de referencia — con cita o sin respuesta."}
        </span>
        <span className={collection ? "corpus-pill on" : "corpus-pill"}>
          {collection ? `● ${collection.label}` : collections.isPending ? "Consultando biblioteca…" : "Biblioteca no disponible"}
        </span>
      </div>
      <RagConnectionSettings />

      <div className="card consulta-card">
        <RagCorpusNotice data={collections.data} />
        <form
          className="consulta-form"
          onSubmit={(e) => {
            e.preventDefault();
            submit(question);
          }}
        >
          <input
            className="consulta-input"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={isPublic ? "Pregunta por el modelo o su metodología…" : "Escribe tu pregunta de economía…"}
            disabled={busy || !collection}
            aria-label="Pregunta económica"
            autoFocus
          />
          <button
            type="submit"
            className="consulta-btn"
            disabled={busy || !collection || question.trim().length < 2}
          >
            {busy ? "…" : "Preguntar"}
          </button>
        </form>

        {!asked && (
          <ul className="consulta-examples">
            {(isPublic ? PUBLIC_RAG_EXAMPLES : EXAMPLES).map((ex) => (
              <li key={ex}>
                <button
                  type="button"
                  className="example-chip"
                  disabled={busy || !collection}
                  onClick={() => submit(ex)}
                >
                  {ex}
                </button>
              </li>
            ))}
          </ul>
        )}

        {displayedFailure && (
          <div className="banner err" role="alert">
            No se pudo consultar la biblioteca: {displayedFailure.detail}
          </div>
        )}
        {collections.isSuccess && !collection && (
          <div className="banner">El servicio no anuncia ninguna colección con pasajes disponibles.</div>
        )}

        {asked && (
          <div className="consulta-thread">
            <p className="consulta-q">
              <strong>Pregunta:</strong> {asked}
            </p>

            {(answerText || busy) && (
              <div ref={answerRef} className="consulta-a">
                {answerText
                  ? answerText.split("\n").map((line, i) => (
                      <p key={i}>{line}</p>
                    ))
                  : <span className="thinking">Buscando en el corpus…</span>}
                {busy && answerText && <span className="cursor">▌</span>}
              </div>
            )}

            {passages.length > 0 && (
              <details className="consulta-passages">
                <summary>
                  {passages.length} {passages.length === 1 ? "fuente" : "fuentes"}
                </summary>
                <ol className="passages-list">
                  {passages.map((p, i) => (
                    <li key={i} className={`psg ${p.authority}`}>
                      <span className="psg-cite">{p.cita}</span>
                      <span className={`psg-auth ${p.authority}`}>
                        {AUTHORITY_LABEL[p.authority] ?? p.authority}
                      </span>
                      <p className="psg-text">{p.text}</p>
                    </li>
                  ))}
                </ol>
              </details>
            )}

            {answer?.error && (
              <p className="consulta-err">⚠ {answer.error}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
