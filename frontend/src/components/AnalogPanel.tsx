import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import type { AnalogResponse, AnalogRequest } from "../api/types";
import { API_BASE } from "../api/client";
import type { Levers } from "../engine/levers";
import { AnalogCard } from "./AnalogCard";

async function fetchAnalog(req: AnalogRequest): Promise<AnalogResponse> {
  const r = await fetch(`${API_BASE}/scenario/analog`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

export function AnalogPanel({
  levers,
  horizon,
}: {
  levers: Partial<Levers>;
  horizon: number;
}) {
  const [open, setOpen] = useState(true);

  const mut = useMutation({
    mutationFn: (request: AnalogRequest) => fetchAnalog(request),
  });

  function handleSearch() {
    setOpen(true);
    mut.mutate({ levers, horizon });
  }

  const key = (r: AnalogRequest) => JSON.stringify([r.horizon, Object.entries(r.levers ?? {}).sort()]);
  const stale = mut.data && mut.variables && key(mut.variables) !== key({ levers, horizon });

  return (
    <div className="card" style={{ marginTop: 24 }}>
      <div
        style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}
        onClick={() => setOpen((v) => !v)}
        role="button"
        aria-expanded={open}
      >
        <h3 style={{ margin: 0 }}>Análogos históricos</h3>
        <span style={{ fontSize: 18 }}>{open ? "▲" : "▼"}</span>
      </div>

      {open && (
        <div style={{ marginTop: 12 }}>
          {!mut.data && !mut.isPending && !mut.isError && (
            <div>
              <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 8 }}>
                Busca los 3 episodios históricos más similares al escenario activo y muestra
                su evolución posterior. La semejanza histórica no predice la trayectoria de España.
              </p>
              <button
                aria-label="Buscar análogo histórico"
                onClick={(e) => { e.stopPropagation(); handleSearch(); }}
                style={{
                  padding: "8px 20px",
                  borderRadius: 6,
                  border: "none",
                  background: "var(--accent, #3b82f6)",
                  color: "#fff",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Buscar análogo histórico
              </button>
            </div>
          )}

          {mut.isPending && (
            <p style={{ fontSize: 14, color: "var(--muted)" }} role="status">
              Buscando episodios históricos…
            </p>
          )}

          {mut.isError && (
            <p style={{ color: "var(--err, #ef4444)", fontSize: 13 }}>
              Error al buscar análogos: {String(mut.error)}
            </p>
          )}

          {mut.data && (
            <>
              {!mut.data.rag_available && (
                <p style={{ fontSize: 11, color: "var(--muted)", marginBottom: 8 }}>
                  Descripción determinista basada en datos históricos.
                </p>
              )}
              <p className="src">Consulta del escenario en {mut.data.query_year ?? horizon} ·
                deuda, saldo total, crecimiento real, paro e inflación. {mut.data.limitations}</p>
              {stale && <p role="status">Estos resultados corresponden a un escenario anterior.
                Actualiza la búsqueda para aplicar los cambios.</p>}
              <AnalogCard matches={mut.data.matches} />
              <button onClick={handleSearch} disabled={mut.isPending}>Actualizar búsqueda</button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
