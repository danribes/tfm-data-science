import { useState, useRef, useEffect } from "react";
import { ragChatStream, setApiBase, API_BASE, DEFAULT_API_BASE } from "../api/client";
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

  const [tunnel, setTunnel] = useState(
    API_BASE === DEFAULT_API_BASE ? "" : API_BASE,
  );
  const [linked, setLinked] = useState(API_BASE !== DEFAULT_API_BASE);
  const [showLink, setShowLink] = useState(false);

  const connect = () => {
    const url = tunnel.trim().replace(/\/+$/, "");
    if (!url) return;
    setApiBase(url);
    setTunnel(url);
    setLinked(true);
    setFailure(null);
  };

  const disconnect = () => {
    setApiBase(null);
    setTunnel("");
    setLinked(false);
    setFailure(null);
  };

  const answerText = answer?.answer ?? streamed;

  useEffect(() => {
    if (streamed && answerRef.current) {
      answerRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [streamed]);

  const submit = (q: string) => {
    const text = q.trim();
    if (text.length < 2 || busy) return;
    setAsked(text);
    setQuestion("");
    setAnswer(null);
    setPassages([]);
    setStreamed("");
    setFailure(null);
    setBusy(true);

    ragChatStream(
      { question: text, collection: "libros", top_k: 6 },
      {
        onPassages: (ps) => setPassages(ps),
        onDelta: (piece) => setStreamed((prev) => prev + piece),
        onDone: (final) =>
          setAnswer({
            vintage: "", computed_not_advice: true,
            question: text, collection: "libros",
            answer: final.answer, passages: [],
            grounded: final.grounded, provider: final.provider,
            model: final.model, error: final.error ?? null,
          } as RagChatResponse),
      },
    )
      .catch((e: unknown) => setFailure(toFailure(e)))
      .finally(() => setBusy(false));
  };

  const unavailable = failure?.status === 503;

  return (
    <div className="consulta">
      <div className="head">
        <h1>Consulta económica</h1>
        <span className="meta">
          Respondo con los textos del corpus de referencia — con cita o sin respuesta.
        </span>
      </div>

      <div className="card consulta-card">
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
            placeholder="Escribe tu pregunta de economía…"
            disabled={busy}
            autoFocus
          />
          <button
            type="submit"
            className="consulta-btn"
            disabled={busy || question.trim().length < 2}
          >
            {busy ? "…" : "Preguntar"}
          </button>
        </form>

        {!asked && (
          <ul className="consulta-examples">
            {EXAMPLES.map((ex) => (
              <li key={ex}>
                <button
                  type="button"
                  className="example-chip"
                  onClick={() => submit(ex)}
                >
                  {ex}
                </button>
              </li>
            ))}
          </ul>
        )}

        {failure && (
          <div className="banner err">
            {unavailable ? (
              <>
                La biblioteca no está disponible en este despliegue público: el
                corpus con derechos de autor y su índice vectorial viven sólo en
                la máquina local.{" "}
                <button
                  type="button"
                  className="link-btn"
                  onClick={() => setShowLink(true)}
                >
                  Conectar con la máquina local
                </button>{" "}
                si tienes la dirección del túnel.
              </>
            ) : (
              `Error: ${failure.detail}`
            )}
          </div>
        )}

        {(showLink || linked) && (
          <div className={linked ? "tunnel on" : "tunnel"}>
            <label className="tunnel-lab" htmlFor="tunnel-url">
              Corpus local — dirección del túnel
            </label>
            <div className="tunnel-row">
              <input
                id="tunnel-url"
                className="tunnel-input"
                value={tunnel}
                onChange={(e) => setTunnel(e.target.value)}
                placeholder="https://algo-aleatorio.trycloudflare.com"
                spellCheck={false}
              />
              {linked ? (
                <button type="button" className="tunnel-btn off" onClick={disconnect}>
                  Desconectar
                </button>
              ) : (
                <button
                  type="button"
                  className="tunnel-btn"
                  onClick={connect}
                  disabled={!tunnel.trim()}
                >
                  Conectar
                </button>
              )}
            </div>
            <p className="tunnel-note">
              {linked ? (
                <>
                  Conectado a <code>{API_BASE}</code>. El corpus se sirve desde
                  la máquina local y sólo responde mientras el túnel esté
                  abierto.
                </>
              ) : (
                <>
                  Los libros tienen derechos de autor y no se publican: se
                  consultan a través de un túnel temporal a la máquina donde
                  vive el índice.
                </>
              )}
            </p>
          </div>
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
