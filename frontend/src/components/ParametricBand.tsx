import { useParametric } from "../api/hooks";
import { eur, nf } from "../lib/fmt";
import { Caption } from "./Caption";
import { FanChart } from "./FanChart";
import { IPV_NOMBRE } from "../lib/glosario";
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
      {/* El encabezado decía «Cuánto de esto es incertidumbre · 4.000 sorteos ·
          semilla 42». El número de sorteos y la semilla sirven para reproducir
          el resultado, no para entenderlo, y ocupaban el sitio de la
          explicación. Van ahora con el resto de la trazabilidad, más abajo. */}
      <h4>
        El margen del precio de la vivienda
        <small>cuánto se mueve la proyección si los parámetros estimados no son exactos</small>
      </h4>

      <p className="band-intro">
        Dos números del motor —cuánto crece el precio a largo plazo y con qué
        rapidez vuelve a esa tendencia— <b>se estimaron a partir de datos</b>, y
        toda estimación tiene margen de error. La banda responde a una sola
        pregunta: si en vez de dar esos dos números por exactos se tiene en
        cuenta su margen, ¿cuánto se mueve la proyección? En 2026 nada, porque
        es el punto de partida. En 2050 la banda abarca un 17 % del precio
        proyectado, algo más de un ±8 % a cada lado: es la columna «sobre el
        nivel» de la tabla.
      </p>

      {q.isPending && !d && <p style={{ fontSize: 14 }}>Sorteando parámetros…</p>}

      {d && (
        <>
          <FanChart years={d.years} percentiles={d.percentiles} center={d.point}
            centerLabel="la proyección publicada"
            outerLabel="9 de cada 10 sorteos (p5–p95)"
            innerLabel="la mitad central (p25–p75)"
            dec={0} unit="€"
            /* Las mismas marcas que las columnas de la tabla de abajo: así se
               puede seguir una cifra del gráfico a la tabla sin recontar. */
            ticks={TABLE_YEARS} />

          {/* El gráfico no decía qué estaba dibujando. */}
          <div className="foot">
            Precio medio de una vivienda, en euros. La banda nace cerrada en
            2026 —ese año es el punto de partida, no hay nada que sortear— y se
            abre a medida que el margen de los dos parámetros se arrastra año
            tras año.
          </div>

          <div className="tscroll">
            <table className="projtable">
              <thead>
                <tr>
                  <th>Año</th>
                  <th className="num">mínimo<small>p5</small></th>
                  <th className="num">proyección</th>
                  <th className="num">máximo<small>p95</small></th>
                  <th className="num">ancho</th>
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
            exactamente. Se sortean {eur(d.n_draws)} veces —con semilla {d.seed}, de
            modo que el resultado se reproduce— de su distribución.
            {lr && rev ? (
              <> Son dos: la subida media anual del precio observada en el panel,
                que el motor usa como destino a largo plazo (<code>IPV_LR</code> ={" "}
                {nf(lr.value, 4)} %, error estándar {nf(lr.se, 4)}), y la parte de
                cada desviación que se corrige en un año (<code>IPV_REV</code> ={" "}
                {nf(rev.value, 4)}, error estándar {nf(rev.se, 4)}), ambas estimadas
                sobre {eur(lr.n)} observaciones trimestrales del {IPV_NOMBRE} (IPV)
                del INE en {lr.n_units} territorios: las comunidades autónomas, Ceuta
                y Melilla.</>
            ) : null}
            {" "}Cada sorteo se mantiene fijo los veinticinco años, porque un
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
