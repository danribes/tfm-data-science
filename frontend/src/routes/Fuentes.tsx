import { useState } from "react";
import snapshot from "../data/fuentes.json";
import { nf } from "../lib/fmt";

/** «Estado de las fuentes»: what the last check found, and what importing
 *  would take.
 *
 *  Static on purpose. The page reads a committed snapshot written by
 *  tools/gen_sources_status.py, never the network: the app computes with the
 *  frozen vintage until a person promotes a new one, and a dashboard that
 *  refreshed by itself would suggest otherwise. The import button is a
 *  prototype and says so — it lays out the steps a real import would take
 *  instead of pretending one happened. */

type Signal = "same_size" | "size_changed" | "unchanged" | "changed" | "error" | "new" | "missing" | "derived";

const SIGNAL: Record<Signal, { label: string; warn: boolean }> = {
  size_changed: { label: "tamaño distinto: revisar", warn: true },
  changed: { label: "cambiada (huella): revisar", warn: true },
  new: { label: "fuente nueva: revisar", warn: true },
  missing: { label: "ya no está: revisar", warn: true },
  error: { label: "error de descarga", warn: true },
  same_size: { label: "mismo tamaño", warn: false },
  unchanged: { label: "sin cambios (huella)", warn: false },
  derived: { label: "se reconstruye al promover", warn: false },
};

const ORDER: Signal[] = ["error", "missing", "changed", "size_changed", "new", "same_size", "unchanged", "derived"];

const PROCEDURE = "https://github.com/danribes/tfm-data-science/blob/main/docs/ACTUALIZAR_DATOS.md";
const INVENTORY = "https://github.com/danribes/tfm-data-science/blob/main/data/README.md";

const bytes = (b: number | null) => (b === null ? "—" : `${nf(b, 0)} B`);

const INVENTORY_LABEL: Record<string, string> = {
  manifest: "descargable",
  original: "registro de julio",
};

export default function Fuentes() {
  const [reviewed, setReviewed] = useState(false);
  const [open, setOpen] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const { vintage, checked, counts, catalog } = snapshot;
  const nAll = catalog.sources.length;
  const agencies = Object.entries(catalog.by_agency);
  const nOriginal = catalog.sources.filter((s) => s.inventory === "original").length;
  const maxRepeats = Math.max(...catalog.sources.map((s) => s.downloads));
  const sources = [...snapshot.sources].sort(
    (a, b) => ORDER.indexOf(a.signal as Signal) - ORDER.indexOf(b.signal as Signal));

  return (
    <div className="guide">
      <div className="head">
        <h1>Estado de las fuentes</h1>
        <span className="meta">vintage en uso {vintage} · última comprobación {checked}</span>
      </div>

      {/* Sin esta frase la página se lee como el inventario de todo lo que
          alimenta el modelo, y no lo es. */}
      <section className="card guide-s">
        <p>
          Esta página sólo comprueba las {counts.sources} fuentes descargables del manifiesto. De
          ellas salen la mayoría de los valores de partida, pero no todo lo que usa el motor: la
          senda central de deuda, las proyecciones demográficas y el panel regional de vivienda
          con el que se estiman sus dos parámetros no se comprueban aquí. El inventario completo,
          capa por capa y con los huecos declarados, está en{" "}
          <a href={INVENTORY} target="_blank" rel="noreferrer">data/README.md</a>.
        </p>
      </section>

      <div className="outs outs-4" role="group" aria-label="Resumen de la comprobación">
        <div className="out">
          <span className="o-label">Vintage en uso</span>
          <span className="o-val o-date">{vintage}</span>
          <span className="o-delta">congelado: con él se calcula todo</span>
        </div>
        <div className="out">
          <span className="o-label">Última comprobación</span>
          <span className="o-val o-date">{checked}</span>
          <span className="o-delta">descarga manual, fuera del vintage</span>
        </div>
        <div className="out">
          <span className="o-label">Fuentes descargadas</span>
          <span className="o-val">{`${counts.ok}/${counts.sources}`}</span>
          <span className={`o-delta${counts.error ? " bad" : ""}`}>
            {counts.error} {counts.error === 1 ? "error" : "errores"} · {counts.derived} derivadas aparte
          </span>
        </div>
        <div className="out">
          <span className="o-label">A revisar</span>
          <span className="o-val">{String(counts.attention)}</span>
          <span className={`o-delta${counts.attention ? " bad" : ""}`}>fuentes con señal de cambio</span>
        </div>
      </div>

      <section className="card guide-s">
        <h2>Fuente por fuente</h2>
        <div className="tscroll">
          <table className="guide-t">
            <thead>
              {/* La señal va antes que el tamaño: es lo que se viene a mirar, y en
                  un teléfono las últimas columnas quedan fuera de la pantalla. */}
              <tr><th>Serie</th><th>Señal</th><th>Tamaño: vintage → comprobación</th><th>Organismo</th></tr>
            </thead>
            <tbody>
              {sources.map((s) => {
                const sig = SIGNAL[s.signal as Signal];
                return (
                  <tr key={s.file} className={s.kind === "derived" ? "dim" : undefined}>
                    <td>{s.series}</td>
                    <td>{sig.warn ? <span className="tag warn">{sig.label}</span> : sig.label}</td>
                    <td>{bytes(s.bytes_before)} → {bytes(s.bytes_after)}</td>
                    <td>{s.agency}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p>
          El vintage congelado no guardó la huella sha256 de la mayoría de sus descargas, así que
          para esas fuentes sólo se puede comparar el tamaño del fichero, y un tamaño distinto es una
          pista, no una prueba: puede ser un dato nuevo, una revisión o sólo un cambio de formato. Un
          tamaño igual tampoco garantiza que nada haya cambiado. La comparación exacta existe desde el
          primer vintage que se promueva con huellas.
        </p>
      </section>

      <section className="card guide-s">
        <h2>Importar un vintage nuevo</h2>
        <p>
          La aplicación calcula con el vintage {vintage} hasta que una persona decida promover uno
          nuevo. Marca la casilla sólo si has revisado las fuentes señaladas y alguno de los cambios
          importa.
        </p>
        <label className="fuentes-check">
          <input type="checkbox" checked={reviewed} onChange={(e) => setReviewed(e.target.checked)} />
          He revisado las fuentes marcadas y hay cambios que importan
        </label>
        <div className="fuentes-import">
          <button
            type="button"
            className="consulta-btn"
            disabled={!reviewed}
            aria-expanded={open}
            onClick={() => setOpen(true)}
          >
            Importar datos nuevos
          </button>
          <span className="tag warn">prototipo</span>
        </div>

        {open && (
          <div className="fuentes-panel" role="region" aria-label="Qué haría la importación">
            <p>
              <strong>Prototipo:</strong> este botón no importa nada. La aplicación sigue calculando
              con el vintage {vintage}.
            </p>
            <p>En la versión real, pulsarlo abriría una propuesta de actualización para revisión:</p>
            <ol className="guide-chain">
              <li>Decidir, fuente por fuente, si el cambio es una revisión o un dato nuevo, y hasta dónde llega ahora la serie.</li>
              <li>Promover el vintage: copiar los datos a data/gold, fecharlo y guardar la huella sha256 de cada fuente.</li>
              <li>Recalcular en orden, empezando por los dos parámetros estimados de la vivienda.</li>
              <li>Pasar las pruebas: anclas del motor, artefactos verificados y paridad entre Python y TypeScript.</li>
              <li>Reescribir lo que haya dejado de ser cierto en la memoria y en la aplicación.</li>
            </ol>
            <p>
              El primer paso no se automatiza: es donde automatizar significaría afirmar algo que nadie
              ha comprobado. El procedimiento completo está en{" "}
              <a href={PROCEDURE} target="_blank" rel="noreferrer">ACTUALIZAR_DATOS.md</a>.
            </p>
          </div>
        )}
      </section>

      <section className="card guide-s">
        <h2>Todas las fuentes de datos</h2>
        <p>{nAll} fuentes de datos distintas, de {agencies.length} organismos.</p>
        <ul className="fuentes-agencies" aria-label="Fuentes por organismo">
          {agencies.map(([agency, k]) => (
            <li key={agency}>{agency} <strong>{k}</strong></li>
          ))}
        </ul>
        <p>
          El registro de julio tiene {catalog.downloads} descargas pero sólo {nOriginal} fuentes
          distintas: algunos ficheros se descargaron varias veces, hasta {maxRepeats}. Varias
          series de Eurostat comparten el mismo enlace porque el registro no anotó sus
          parámetros; se distinguen por el nombre. A ellas se suman las {counts.sources} fuentes
          descargables del manifiesto, que no coinciden con ninguna. Los ficheros crudos de
          entonces no se conservaron: lo congelado son las tablas construidas con ellos.
        </p>
        <div>
          <button
            type="button"
            className="consulta-btn"
            aria-expanded={showAll}
            aria-controls="fuentes-todas"
            onClick={() => setShowAll((v) => !v)}
          >
            {showAll ? `Ocultar las ${nAll} fuentes` : `Ver las ${nAll} fuentes`}
          </button>
        </div>

        {showAll && (
          <div className="tscroll fuentes-todas" id="fuentes-todas">
            <table className="guide-t" aria-label="Todas las fuentes de datos">
              <thead>
                <tr>
                  <th>Fuente (enlace al origen)</th><th>Organismo</th><th>Inventario</th>
                  <th>Descargas</th><th>Tamaño</th><th>Fecha</th>
                </tr>
              </thead>
              <tbody>
                {catalog.sources.map((s) => (
                  <tr key={`${s.url}#${s.name}`}>
                    <td><a href={s.url} title={s.url} target="_blank" rel="noreferrer">{s.name}</a></td>
                    <td>{s.agency}</td>
                    <td className="nowrap">{INVENTORY_LABEL[s.inventory] ?? s.inventory}</td>
                    <td className="nowrap">{s.downloads}</td>
                    <td className="nowrap">{bytes(s.bytes)}</td>
                    <td className="nowrap">{s.fetched}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
