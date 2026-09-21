import { Fragment } from "react";
import { LEVER_SPECS, isMoved, type Levers } from "../engine/levers";
import { BASE_LEVERS } from "../engine/vintage";
import { Y0, baseline, type Scenario } from "../engine/spain";
import { eur, nf, sg, sgEur } from "../lib/fmt";
import { SERIES_FORMAT, UP_IS_BAD } from "./KpiRow";
import { PANEL_DEPENDENT, SIDES, TABLE_ROWS, TABLE_YEARS, tone } from "../lib/seriesMeta";

/** Qué has cambiado. Sin esto, quien llega desde un enlace con palancas
 *  movidas no tiene forma de saber qué escenario está mirando. */
export function LeverSummary({ levers }: { levers: Levers }) {
  const moved = LEVER_SPECS.filter((s) => isMoved(levers, s.id));
  return (
    <div className="lever-summary">
      {moved.length === 0 ? (
        <span className="muted">Nada movido: esto es la línea base del vintage.</span>
      ) : (
        moved.map((s) => (
          <span className="lever-pill" key={s.id}>
            {s.nm} {nf(BASE_LEVERS[s.id], s.dec)} → {nf(levers[s.id], s.dec)} {s.unit}
          </span>
        ))
      )}
      {moved.length > 0 && <span className="muted">todo lo demás, en su valor observado</span>}
    </div>
  );
}

/** El futuro en números.
 *
 *  La página no tenía tabla: sólo gráficos y fichas. Un gráfico responde «hacia
 *  dónde» y una tabla responde «cuánto», y la segunda pregunta es la que se
 *  hace cualquiera que vaya a citar una cifra.
 *
 *  Dos marcas que evitan malentendidos concretos:
 *
 *  · las series sin senda propia se señalan. `u` y `pi` son constantes en los
 *    veinticinco años de la línea base — el motor no les da trayectoria, sólo
 *    un desplazamiento en bloque— y ver esa recta sin explicación es lo que
 *    hace pensar que la herramienta está rota.
 *
 *  · la procedencia va por fila. Casi todo sale de una identidad contable con
 *    reglas calibradas; sólo la cadena de vivienda lleva dos parámetros
 *    estimados de datos. Decirlo por fila es más honesto que una nota al pie.
 */
export function ProjectionTable({ scn }: { scn: Scenario }) {
  const base = baseline();
  return (
    <div className="tscroll">
      <table className="projtable">
        <thead>
          <tr>
            <th rowSpan={2}>Serie</th>
            {/* 2026 es el PRIMER AÑO PROYECTADO, no un dato observado. El
                motor aplica las palancas ya en k=0: la línea base da 106,32
                partiendo del 105,6 observado de 2025, y una palanca lo mueve a
                105,81. Decía «· hoy», que invitaba a leerlo como dato, y la
                columna traía una Δ distinta de cero que lo desmentía. */}
            {TABLE_YEARS.map((y) => (
              <th key={y} className={`num grp${y === Y0 ? " obs" : ""}`} colSpan={2}>
                {y}{y === Y0 ? " · inicio" : ""}
              </th>
            ))}
          </tr>
          {/* Segunda fila: la cabecera decía «2030» sobre dos columnas y nada
              indicaba que la segunda era la diferencia. Estaba explicado en
              prosa debajo de la tabla, que es donde no se mira. */}
          <tr className="sub">
            {TABLE_YEARS.map((y) => (
              <Fragment key={`s-${y}`}>
                <th className={`num grp${y === Y0 ? " obs" : ""}`}>valor</th>
                <th className={`num${y === Y0 ? " obs" : ""}`}>Δ base</th>
              </Fragment>
            ))}
          </tr>
        </thead>
        <tbody>
          {TABLE_ROWS.map(({ k, lab, plain }) => {
            const f = SERIES_FORMAT[k] ?? { dec: 1, unit: "" };
            const b = base[k], s = scn[k];
            if (!b || !s) return null;
            const pinned = Math.max(...b) - Math.min(...b) < 1e-9;
            const panel = PANEL_DEPENDENT.has(k);
            return (
              <tr key={k}>
                <th scope="row">
                  {lab}
                  {pinned && (
                    <span className="tag warn" title="El motor no le da senda propia: se queda en su valor observado y sólo se desplaza en bloque cuando una palanca la empuja">
                      sin senda propia
                    </span>
                  )}
                  {k in SIDES && (
                    <span className="tag rel" title={`Subir es buena noticia para ${SIDES[k][0]} y mala para ${SIDES[k][1]}`}>
                      signo según quién pregunte
                    </span>
                  )}
                  {/* Qué mide la fila, sin jerga, en su propia línea y después
                      de las etiquetas: éstas matizan el nombre y deben quedar
                      junto a él. Un lector que no sabe qué es un saldo primario
                      no puede juzgar si +0,6 es mucho. */}
                  <span className="plain">{plain}</span>
                  <small>
                    {f.unit}
                    {" · "}
                    <span className={`tag prov ${panel ? "panel" : "motor"}`}
                      title={panel
                        ? "Dos constantes estimadas con econometría de panel entran en esta cadena"
                        : "Identidad contable y reglas calibradas: ningún modelo aprendido interviene"}>
                      {panel ? "motor + panel" : "motor"}
                    </span>
                  </small>
                </th>
                {TABLE_YEARS.map((y) => {
                  const i = y - Y0;
                  const delta = s[i] - b[i];
                  return (
                    <Fragment key={`${k}-${y}`}>
                      {/* Sin decimales significa magnitud grande —euros,
                          recuentos— y ahí el separador de millares va siempre:
                          `nf` lo suprime entre 1000 y 9999 y la columna
                          mezclaba "1033" con "171.444". */}
                      <td className={`num grp${y === Y0 ? " obs" : ""}`}>
                        {f.dec === 0 ? eur(s[i]) : nf(s[i], f.dec)}
                      </td>
                      <td className={`num d ${tone(delta, k, UP_IS_BAD.has(k))}${y === Y0 ? " obs" : ""}`}>
                        {f.dec === 0 ? sgEur(delta) : sg(delta, f.dec)}
                      </td>
                    </Fragment>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
