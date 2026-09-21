import { useParametric } from "../api/hooks";
import { eur, nf } from "../lib/fmt";
import { Caption } from "./Caption";
import { FanChart } from "./FanChart";
import { TABLE_YEARS } from "../lib/seriesMeta";
import { useScenarioStore } from "../state/scenarioStore";

/** La incertidumbre que sí puede medirse, y sólo donde puede medirse.
 *
 *  El abanico de deuda simula choques sobre tipos, crecimiento y saldo
 *  primario. Ninguna de sus constantes procede de una estimación: son
 *  calibraciones, y sortearlas sería inventar una distribución que nadie ha
 *  estimado. Del motor entero sólo dos parámetros tienen error típico, y los
 *  dos actúan sobre la vivienda. Por eso esta banda está aquí y no allí.
 */
export function ParametricBand() {
  const levers = useScenarioStore((s) => s.levers);
  const q = useParametric(levers, "precio");

  if (q.isError) {
    return (
      <div className="card">
        <h4>Cuánto de esto es incertidumbre</h4>
        <div className="banner err">
          Banda paramétrica no disponible — el resto de la página sigue funcionando.
        </div>
      </div>
    );
  }

  const d = q.data;
  const lr = d?.params?.IPV_LR;
  const rev = d?.params?.IPV_REV;

  return (
    <div className="card">
      <h4>
        Cuánto de esto es incertidumbre
        <small>{d ? `${eur(d.n_draws)} sorteos · semilla ${d.seed}` : "precio de la vivienda"}</small>
      </h4>

      {q.isPending && !d && <p style={{ fontSize: 14 }}>Sorteando parámetros…</p>}

      {d && (
        <>
          <FanChart years={d.years} percentiles={d.percentiles} center={d.point}
            centerLabel="proyección con los valores puntuales" dec={0} unit="€"
            /* Las mismas marcas que las columnas de la tabla de abajo: así se
               puede seguir una cifra del gráfico a la tabla sin recontar. */
            ticks={TABLE_YEARS} />

          <div className="tscroll">
            <table className="projtable">
              <thead>
                <tr>
                  <th>Año</th><th className="num">p5</th><th className="num">proyección</th>
                  <th className="num">p95</th><th className="num">ancho</th>
                  <th className="num">sobre el nivel</th>
                </tr>
              </thead>
              <tbody>
                {TABLE_YEARS.map((y) => {
                  const i = d.years.indexOf(y);
                  if (i < 0) return null;
                  const ancho = d.percentiles.p95[i] - d.percentiles.p5[i];
                  const rel = d.point[i] ? (ancho / d.point[i]) * 100 : 0;
                  return (
                    <tr key={y}>
                      <th scope="row">{y}</th>
                      <td className="num">{eur(d.percentiles.p5[i])}</td>
                      <td className="num"><b>{eur(d.point[i])}</b></td>
                      <td className="num">{eur(d.percentiles.p95[i])}</td>
                      <td className="num d">{eur(ancho)}</td>
                      <td className="num d">{nf(rel, 1)} %</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <Caption>
            <strong>Qué mide esta banda.</strong> Una sola cosa: que los dos
            parámetros del motor que vienen de una estimación no se conocen
            exactamente. Se sortean {eur(d.n_draws)} veces de su distribución
            {lr && rev ? (
              <> — IPV_LR {nf(lr.value, 4)} (se {nf(lr.se, 4)}), IPV_REV {nf(rev.value, 4)}{" "}
                (se {nf(rev.se, 4)}), estimadas sobre {eur(lr.n)} observaciones
                trimestrales de {lr.n_units} comunidades</>
            ) : null}
            {" "}y cada sorteo se mantiene fijo los veinticinco años, porque un
            parámetro es una incógnita fija y no un choque anual. La línea
            central sigue siendo la proyección publicada, no la mediana de los
            sorteos.
          </Caption>
          <Caption>
            <strong>Qué no es.</strong> No es un intervalo de predicción: no
            incluye el error del propio modelo, ni cambios estructurales, ni la
            incertidumbre de las palancas, que las fijas tú.{" "}
            <strong>Un precio fuera de esta cinta no contradice al modelo.</strong>
          </Caption>
          <Caption>
            <strong>Por qué sólo la vivienda.</strong> De las series de la tabla
            de arriba, la cadena de vivienda es la única que depende de
            parámetros estimados. El resto sale de una identidad contable y de
            reglas calibradas: no tienen error típico que sortear, y dibujarles
            una banda sería inventarse una distribución. El abanico de la deuda
            existe, pero mide otra cosa —choques sobre tipos, crecimiento y
            saldo primario— y no es comparable con ésta.
          </Caption>
        </>
      )}
    </div>
  );
}
