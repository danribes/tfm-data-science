import { useEffect, useState } from "react";
import { DEFAULT_RAG_API_BASE, setRagConnection } from "../api/client";
import { useRagConnection } from "../api/hooks";

/** Optional private library connection. Public/default libraries need no setup. */
export function RagConnectionSettings() {
  const connection = useRagConnection();
  const [url, setUrl] = useState(connection.customBaseUrl ?? "");
  const [token, setToken] = useState("");
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    setUrl(connection.customBaseUrl ?? "");
    setToken("");
    setError(null);
  }, [connection]);

  return (
    <details className="card">
      <summary>Conexión de biblioteca</summary>
      <p>Servicio: <code>{connection.baseUrl}</code>. Esta conexión sólo afecta a la biblioteca.</p>
      <form onSubmit={(event) => {
        event.preventDefault();
        try {
          setRagConnection(url || null, token);
          setError(null);
        } catch (cause) {
          setError(cause instanceof Error ? cause.message : String(cause));
        }
      }}>
        <label className="rag-connection-label">
          Dirección de otra biblioteca (opcional)
          <input className="rag-connection-input" value={url} onChange={(event) => setUrl(event.target.value)}
            placeholder={DEFAULT_RAG_API_BASE} spellCheck={false} autoComplete="off" />
        </label>
        <label className="rag-connection-label">
          Token de acceso (opcional, sólo esta sesión)
          <input className="rag-connection-input" type="password" value={token}
            onChange={(event) => setToken(event.target.value)} autoComplete="off" />
        </label>
        {connection.hasToken && <p>Hay un token activo para esta sesión. Al guardar, el campo vacío lo elimina.</p>}
        <button type="submit" className="rag-connection-button">Guardar conexión</button>{" "}
        {connection.customBaseUrl && (
          <button type="button" className="rag-connection-button off" onClick={() => setRagConnection(null)}>
            Usar biblioteca predeterminada
          </button>
        )}
        {error && <p className="rag-connection-error" role="alert">{error}</p>}
      </form>
    </details>
  );
}
