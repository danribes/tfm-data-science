import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { IrfChart } from "../components/IrfChart";
import type { ComparisonOut } from "../api/types";
import { nf, sg } from "../lib/fmt";

/** A calibrated value against its estimated confidence band.
 *
 *  Drawn to scale so the reader can see *how far* outside the band a
 *  calibration falls, not just that it does. A table of numbers would make a
 *  near-miss and a threefold gap look identical. */
function BandBar({ c }: { c: ComparisonOut }) {
  const lo = Math.min(c.ci_low, c.calibrated, c.coef);
  const hi = Math.max(c.ci_high, c.calibrated, c.coef);
  const pad = (hi - lo) * 0.15 || 0.1;
  const min = lo - pad;
  const span = hi - min + pad || 1;
  const pct = (v: number) => ((v - min) / span) * 100;

  return (
    <div className="band">
      <span className="band-track">
        <span
          className="band-ci"
          style={{ left: `${pct(c.ci_low)}%`, width: `${pct(c.ci_high) - pct(c.ci_low)}%` }}
          title={`banda 90 %: ${nf(c.ci_low, 2)} – ${nf(c.ci_high, 2)}`}
        />
        <span className="band-est" style={{ left: `${pct(c.coef)}%` }}
              title={`estimado ${nf(c.coef, 2)}`} />
        <span
          className={c.compatible ? "band-cal ok" : "band-cal bad"}
          style={{ left: `${pct(c.calibrated)}%` }}
          title={`calibrado ${nf(c.calibrated, 2)}`}
        />
      </span>
    </div>
  );
}

export default function Evidencia() {
  const q = useQuery({ queryKey: ["evidence"], queryFn: api.evidence, staleTime: Infinity });

  const blocked = Object.entries(q.data?.identifiable ?? {}).filter(([, v]) => v.startsWith("no"));
  const ok = Object.entries(q.data?.identifiable ?? {}).filter(([, v]) => v.startsWith("sí"));

  return (
    <div className="guide">
      <div className="head">
        <h1>Evidencia</h1>
        <span className="meta">
          {q.data ? `motor v${q.data.engine_version} · vintage ${q.data.vintage}` : "calculando…"}
        </span>
      </div>

      <section className="card guide-s">
        <h2>Qué hace esta página</h2>
        <p>
          En <Link to="/metodologia">Datos y método</Link> se declara que las
          constantes del motor son <strong>calibraciones, no estimaciones</strong>:
          vienen de la literatura y no se han medido sobre estos datos. Esta
          página es la respuesta a esa declaración. Para cada constante que el
          vintage congelado puede juzgar, se estima su valor sobre los paneles
          históricos, se da una banda al 90 % y se dice si la calibración cae
          dentro.
        </p>
        <p>
          Que una calibración quede fuera de la banda <em>no es un error del
          modelo</em>: es un hallazgo, y aquí se publica como tal. Lo que sí
          sería un error es presentar una calibración como si estuviera medida.
        </p>
      </section>

      {q.isError && (
        <div className="banner err">
          No se pudo calcular la capa empírica. ¿Está la API en marcha?
        </div>
      )}
      {q.isPending && <p className="dim">Estimando sobre los paneles…</p>}

      {q.data && (
        <>
          <section className="card guide-s">
            <h2>Calibrado frente a estimado</h2>
            <div className="tscroll">
              <table className="guide-t ev-t">
                <thead>
                  <tr>
                    <th>Constante</th><th>Calibrado</th><th>Estimado</th>
                    <th>Banda 90 %</th><th>Muestra</th><th></th><th>Veredicto</th>
                  </tr>
                </thead>
                <tbody>
                  {q.data.comparisons.flatMap((c) => [
                    <tr key={c.constant}>
                      <td>
                        <code>{c.constant}</code>
                        <div className="dim ev-lab">{c.label}</div>
                      </td>
                      <td className="num">{nf(c.calibrated, 2)}</td>
                      <td className="num">{nf(c.coef, 2)}</td>
                      <td className="num dim">
                        {nf(c.ci_low, 2)} … {nf(c.ci_high, 2)}
                      </td>
                      <td className="num dim">
                        {nf(c.n, 0)}
                        <div className="ev-lab">{c.n_units} unidades</div>
                      </td>
                      <td className="ev-band"><BandBar c={c} /></td>
                      <td>
                        <span className={c.compatible ? "st safe" : "st crossed"}>
                          {c.verdict}
                        </span>
                        <div className="dim ev-lab">{c.source}</div>
                      </td>
                    </tr>,
                    ...c.subperiods.map((s) => {
                      // Recomputed per window: reusing the full-sample verdict
                      // would paint a marker that contradicts its own bar.
                      const fits = s.ci_low <= c.calibrated && c.calibrated <= s.ci_high;
                      return (
                        <tr key={`${c.constant}:${s.label}`} className="ev-sub">
                          <td className="dim">↳ {s.label}</td>
                          <td className="num dim">—</td>
                          <td className="num">{nf(s.coef, 2)}</td>
                          <td className="num dim">
                            {nf(s.ci_low, 2)} … {nf(s.ci_high, 2)}
                          </td>
                          <td className="num dim">{nf(s.n, 0)}</td>
                          <td className="ev-band">
                            <BandBar c={{ ...c, ...s, compatible: fits }} />
                          </td>
                          <td className="dim ev-lab">
                            {fits
                              ? "el valor calibrado cabe en esta ventana"
                              : "el valor calibrado tampoco cabe aquí"}
                          </td>
                        </tr>
                      );
                    }),
                  ])}
                </tbody>
              </table>
            </div>
            <p className="caption">
              La barra clara es la banda al 90 %, el punto oscuro el valor
              estimado y el marcador el valor que usa el motor. Está dibujada a
              escala a propósito: en una tabla de cifras, quedarse fuera por poco
              y quedarse fuera por el triple se leen igual.
            </p>
            <p className="caption">
              Las filas con ↳ son el mismo estimador sobre una ventana más
              corta. Están porque la muestra completa arranca en 2007 y contiene
              entero el pinchazo inmobiliario: promediar la caída y la
              recuperación da una cifra que no describe ninguna de las dos.
              Publicando las mitades, la dependencia de la ventana se ve en vez
              de tener que preguntarse.
            </p>
            <p className="caption">
              Errores estándar agrupados por unidad. Sin agrupar, la fuerte
              autocorrelación dentro de cada región o país haría que casi
              cualquier estimación pareciera significativa.
            </p>
          </section>

          {q.data.irf && (() => {
            const irf = q.data.irf;
            const last = irf.horizons[irf.horizons.length - 1];
            const anchor = irf.horizons.find((p) => p.h === irf.anchor_h);
            const engineLast = irf.engine_path[irf.engine_path.length - 1]?.coef;
            // Same payload as the curve, so the sentence cannot drift from it.
            const rev = q.data.comparisons.find((x) => x.constant === "IPV_REV")
              ?.calibrated ?? 0;
            // Read off the data, not asserted in prose: if a future vintage
            // reverses the sign, the sentence reverses with it.
            const builds = anchor ? last.coef > anchor.coef : false;
            return (
              <section className="card guide-s">
                <h2>Cuánto dura un choque de vivienda</h2>
                <p>
                  <code>IPV_REV</code> es una afirmación sobre dinámica: el
                  motor supone que una desviación del precio se deshace un{" "}
                  {nf(rev * 100, 0)} % cada año. Esta es la versión de los
                  datos. {irf.note}, estimado horizonte a horizonte.
                </p>
                <IrfChart irf={irf} />
                <p>
                  A los {nf(last.years, 0)} años la desviación estimada es de{" "}
                  <strong>{nf(last.coef, 2)}</strong>{" "}
                  <span className="dim">
                    [{nf(last.ci_low, 2)} … {nf(last.ci_high, 2)}]
                  </span>{" "}
                  {irf.unit}
                  {engineLast != null && (
                    <> frente a {nf(engineLast, 2)} bajo el supuesto del motor</>
                  )}
                  .{" "}
                  {builds
                    ? "La respuesta no se deshace: sigue creciendo. En el panel regional, un choque de precios tiene inercia, no reversión."
                    : "La respuesta decae, en línea con lo que supone el motor."}
                </p>
                <p className="caption">
                  Es persistencia, no causalidad estructural: identifica la
                  parte del choque específica de una comunidad, no un
                  experimento. Y mide desviaciones entre CCAA — un choque que
                  suba el precio en toda España a la vez desaparece al restar la
                  media del trimestre, que es precisamente lo que permite
                  estimar el resto.
                </p>
              </section>
            );
          })()}

          {q.data.fiscal_persistence && (
            <section className="card guide-s">
              <h2>Cuánto cuesta mover el saldo público</h2>
              <p>
                El panel de 18 países desde 1960 da una persistencia del saldo
                (ingresos menos gastos) de{" "}
                <strong>{nf(q.data.fiscal_persistence.coef, 2)}</strong>{" "}
                <span className="dim">
                  [{nf(q.data.fiscal_persistence.ci_low, 2)} …{" "}
                  {nf(q.data.fiscal_persistence.ci_high, 2)}], n ={" "}
                  {nf(q.data.fiscal_persistence.n, 0)}
                </span>
                . Es decir: el saldo de un año explica casi todo el del
                siguiente.
              </p>
              <p>
                Esto toca directamente a la palanca <code>sp</code>. El panel te
                deja mover el saldo primario {sg(4, 0)} puntos de PIB y
                mantenerlo veinticinco años; la historia dice que los saldos se
                mueven despacio y vuelven. La aritmética del escenario es
                correcta — la pregunta que abre este número es si el supuesto de
                comportamiento lo es.
              </p>
            </section>
          )}

          <section className="card guide-s">
            <h2>Qué no puede juzgar este vintage</h2>
            <p>
              Se publica junto a los resultados y no en una nota al pie: enseñar
              sólo lo estimable daría una impresión de cobertura que no existe.
              Los motivos son econométricos, no de intendencia.
            </p>
            <ul className="guide-no">
              {blocked.map(([k, v]) => (
                <li key={k}>
                  <code>{k}</code> — {v.replace(/^no — /, "")}
                </li>
              ))}
            </ul>
            {ok.length > 0 && (
              <p className="caption">
                Sí estimables con este corte: {ok.map(([k]) => k).join(" · ")}.
              </p>
            )}
          </section>

          <section className="card guide-s">
            <h2>Cómo leer esto sin pasarse</h2>
            <ul className="guide-no">
              <li>
                <strong>La ventana importa, y por eso está partida.</strong> El
                IPV cae con fuerza hasta 2013 y sube con fuerza después; el 3 %
                que usa el motor no cae en ninguna de las dos ventanas, pero
                queda entre ellas. Una calibración tomada de una historia más
                larga que la del corte no es por ello errónea: responde a otra
                pregunta, la de un ciclo completo.
              </li>
              <li>
                <strong>Esto no es causalidad.</strong> Son medias y
                persistencias condicionadas a efectos fijos, no efectos de un
                shock identificado. Por eso <code>MULT</code> no aparece arriba.
              </li>
              <li>
                <strong>Los números se mueven con el vintage.</strong> Los tests
                fijan sobre todo la maquinaria: que los efectos fijos recuperan
                una pendiente conocida, que agrupar ensancha la banda. Dos
                fijan además el signo de lo que se ve aquí — que la calibración
                del IPV queda fuera de su banda, que el choque no se deshace —
                para que un cambio de corte tenga que revisarse a mano en vez de
                pasar callando. Los coeficientes en sí son propiedad del corte
                de datos.
              </li>
            </ul>
          </section>
        </>
      )}
    </div>
  );
}
