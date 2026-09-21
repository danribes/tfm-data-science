import { useEffect, useRef, useState } from "react";
import { RagReportCard } from "../components/RagReportCard";
import { ragChatStream } from "../api/client";
import { selectRagCollection, useRagCollections, useRagConnection } from "../api/hooks";
import { RagConnectionSettings } from "../components/RagConnectionSettings";
import { PUBLIC_RAG_EXAMPLES, RagCorpusNotice } from "../components/RagCorpusNotice";
import type { Authority, Passage, RagChatResponse } from "../api/types";
import { useScenarioStore } from "../state/scenarioStore";
import { eur } from "../lib/fmt";

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

type Failure = { status?: number; detail: string };

/** Normalise whatever the request layer threw into status + human reason. */
function toFailure(e: unknown): Failure {
  const err = e as { status?: number; detail?: string; message?: string } | null;
  return {
    status: err?.status,
    detail: err?.detail ?? err?.message ?? String(e),
  };
}

export default function Biblioteca() {
  const connection = useRagConnection();
  const collections = useRagCollections();
  const isPublic = collections.data?.corpus_scope === "public_project_docs";
  const collFailure = collections.isError ? toFailure(collections.error) : null;
  const [selectedCollection, setCollection] = useState<string | null>(null);
  const active = collections.data?.collections.find((item) => item.id === selectedCollection)
    ?? selectRagCollection(collections.data?.collections, collections.data?.default_collection);
  const collection = active?.id ?? "";
  const unavailable = !active || active.chunks === 0 || collections.isError;

  const levers = useScenarioStore((s) => s.levers);
  const horizon = useScenarioStore((s) => s.horizon);

  const [question, setQuestion] = useState("");
  const [withScenario, setWithScenario] = useState(false);
  const [answer, setAnswer] = useState<RagChatResponse | null>(null);
  const [passages, setPassages] = useState<Passage[]>([]);
  const [asked, setAsked] = useState("");

  const [streamed, setStreamed] = useState("");
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<Failure | null>(null);

  const controller = useRef<AbortController | null>(null);
  useEffect(() => {
    setCollection(null); setAsked(""); setStreamed(""); setPassages([]); setAnswer(null); setFailure(null); setBusy(false);
    return () => controller.current?.abort();
  }, [connection.revision]);

  const submit = (q: string) => {
    const text = q.trim();
    if (text.length < 2 || busy || unavailable) return;
    setQuestion(text);
    setAsked(text);
    setAnswer(null);
    setPassages([]);
    setStreamed("");
    setFailure(null);
    setBusy(true);

    const request = new AbortController();
    controller.current = request;
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
      request.signal,
    )
      .catch((e: unknown) => { if (!request.signal.aborted) setFailure(toFailure(e)); })
      .finally(() => { if (!request.signal.aborted) setBusy(false); });
  };

  const shown = passages;
  // While streaming, render what has arrived; once done, the final text (they
  // agree, but `done` is authoritative if a provider died mid-stream).
  const answerText = answer?.answer ?? streamed;

  const empty = active && active.chunks === 0;

  return (
    <div className="biblio">
      <div className="head">
        <h1>Biblioteca</h1>
        <span className="meta">
          {collections.isSuccess
            ? `${eur(collections.data.total_documents)} documentos · ${eur(collections.data.total_chunks)} pasajes indexados`
            : collections.isError
              ? "índice no disponible en este despliegue"
              : "cargando el índice…"}
        </span>
      </div>

      <RagConnectionSettings />
      <div className="card">
        <RagCorpusNotice data={collections.data} />
        <p className="biblio-intro">
          {isPublic ? "Pregunta sobre el modelo, sus resultados o su metodología" : "Pregunta sobre economía, estadística o recuperación de información"}
          {" "}y te respondo <strong>a partir de los pasajes
          recuperados</strong>, con referencias a las fuentes. Comprueba que las
          citas respalden la respuesta: la IA puede equivocarse o abstenerse si
          falta información. Las colecciones disponibles dependen del servicio conectado;
          los pasajes seleccionados se envían al proveedor de IA configurado.
        </p>

        <div className="biblio-colls">
          {(collections.data?.collections ?? []).map((c) => (
            <button
              key={c.id}
              type="button"
              className={c.id === collection ? "coll on" : "coll"}
              disabled={busy}
              onClick={() => setCollection(c.id)}
              title={c.note}
            >
              <span className="coll-label">{c.label}</span>
              <span className={`coll-auth ${c.authority}`}>{c.authority}</span>
              <span className="coll-n">{eur(c.chunks)}</span>
            </button>
          ))}
        </div>
        {active && <p className="biblio-note">{active.note}</p>}
        {empty && (
          <div className="banner">
            Esta colección no tiene pasajes disponibles.
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
            placeholder={isPublic ? "¿Qué parámetros del modelo están estimados con datos?" : "¿por qué sube la deuda cuando el tipo supera al crecimiento?"}
            aria-label="Pregunta"
            disabled={unavailable}
          />
          <button type="submit" disabled={unavailable || busy || question.trim().length < 2}>
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
          enlazar las fuentes citadas con los números que hay ahora en pantalla.
        </label>

        <div className="biblio-eg">
          {(isPublic ? PUBLIC_RAG_EXAMPLES : EXAMPLES).map((q) => (
            <button key={q} type="button" onClick={() => submit(q)} disabled={unavailable}>
              {q}
            </button>
          ))}
        </div>
      </div>

      {collFailure && (
        <div className="banner err" role="alert">
          No se pudo cargar el índice de la biblioteca: {collFailure.detail}
        </div>
      )}
      {failure && (
        <div className="banner err" role="alert">
          No se pudo consultar la biblioteca: {failure.detail}
        </div>
      )}
      {collections.isSuccess && !active && (
        <div className="banner">El servicio no anuncia ninguna colección con pasajes disponibles.</div>
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
                Pasajes recuperados{" "}
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
                  pasajes de arriba. Las referencias se comprueban, pero la
                  fidelidad de cada afirmación requiere revisar las fuentes.
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

      <RagReportCard />
    </div>
  );
}
