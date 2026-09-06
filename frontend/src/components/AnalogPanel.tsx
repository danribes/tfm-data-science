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
  const [open, setOpen] = useState(false);

  const mut = useMutation({
    mutationFn: () => fetchAnalog({ levers, horizon }),
  });

  function handleSearch() {
    setOpen(true);
    mut.mutate();
  }

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
                cómo evolucionaron, en qué se diferencia España, y por qué el resultado puede
                converger o divergir.
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
                  ⚠ Análisis narrativo solo disponible en despliegue local.
                </p>
              )}
              <AnalogCard matches={mut.data.matches} />
            </>
          )}
        </div>
      )}
    </div>
  );
}
