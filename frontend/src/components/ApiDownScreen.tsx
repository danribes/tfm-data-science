import { API_BASE, DEFAULT_API_BASE, setApiBase } from "../api/client";

export function ApiDownScreen({ error }: { error: unknown }) {
  return (
    <div className="blocking">
      <div className="card">
        <h4>No se puede conectar con la API</h4>
        <p style={{ fontSize: 12, color: "var(--ink-2)" }}>
          Esta aplicación calcula sobre los datos del servicio de fase 1 y no inventa nada:
          sin API no hay números. Comprueba que el servicio está arrancado en{" "}
          <code>{API_BASE}</code> y recarga.
        </p>
        <p style={{ fontSize: 12 }}>
          Arranque (desde la raíz del repo):{" "}
          <code>uvicorn api.main:app --reload --port 8000</code>
        </p>
        {error instanceof Error && (
          <p className="src" style={{ whiteSpace: "normal" }}>Detalle: {error.message}</p>
        )}
        {API_BASE !== DEFAULT_API_BASE && (
          <p style={{ fontSize: 12, marginTop: 10 }}>
            <button
              type="button"
              className="link-btn"
              onClick={() => {
                setApiBase(null);
                location.reload();
              }}
            >
              Volver a la API pública
            </button>
          </p>
        )}
      </div>
    </div>
  );
}
