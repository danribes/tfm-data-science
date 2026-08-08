import { Link } from "react-router-dom";
import { useRedlines } from "../api/hooks";
import { LEVER_SPECS } from "../engine/levers";
import { BASE_LEVERS, ENGINE_VERSION, VINTAGE } from "../engine/vintage";
import * as C from "../engine/constants";
import { NEAR_FRACTION } from "../engine/redlines";
import { Y0, Y1 } from "../engine/spain";
import { nf } from "../lib/fmt";

/** The guided tour: what the model answers, how a change travels through it,
 *  how to read the fan and the red lines, and what it cannot tell you.
 *
 *  Coefficients and lever ranges are imported from the engine rather than typed
 *  in, so a recalibration updates this page instead of silently making it lie.
 *  The Monte Carlo figures are the server's (the fan is computed in Python);
 *  they are stated the same way Laboratorio states them. */
export default function ComoFunciona() {
  const redlines = useRedlines();

  return (
    <div className="guide">
      <div className="head">
        <h1>Cómo funciona</h1>
        <span className="meta">
          motor v{ENGINE_VERSION} · vintage {VINTAGE}
        </span>
      </div>

      <section className="card guide-s">
        <h2>1. Qué pregunta responde</h2>
        <p>
          Una sola: <strong>¿qué le pasaría a la deuda, al paro, a los precios y
          al esfuerzo de comprar vivienda si algunas condiciones cambiaran y se
          mantuvieran así?</strong>
        </p>
        <p>
          Es una proyección <em>condicional</em>, y la palabra importa. No dice
          qué va a pasar; dice qué implica el modelo si mueves una palanca y la
          dejas quieta. Nadie sabe dónde estará el Euríbor en 2040. Lo que sí se
          puede hacer, y es lo que hace esta herramienta, es ser explícito sobre
          la aritmética que conecta ese tipo con la deuda pública, y enseñar el
          margen de error en vez de esconderlo.
        </p>
      </section>

      <section className="card guide-s">
        <h2>2. La identidad que gobierna todo</h2>
        <p className="guide-eq">b(t+1) = b(t) · (1 + r − g) − sp</p>
        <p>
          La deuda del año que viene es la de este año, capitalizada por la
          diferencia entre lo que cuesta la deuda (<code>r</code>) y lo que crece
          la economía (<code>g</code>), menos el superávit primario
          (<code>sp</code>). Casi todo lo demás en el motor existe para alimentar
          esos tres términos.
        </p>
        <p>
          De ahí sale la intuición central: mientras <code>r</code> sea menor que{" "}
          <code>g</code>, la deuda se diluye sola aunque no haya superávit.
          Cuando <code>r</code> supera a <code>g</code>, hace falta superávit
          primario sólo para que la deuda no crezca.
        </p>
      </section>

      <section className="card guide-s">
        <h2>3. Las diez palancas</h2>
        <p>
          Los rangos no son decorativos: son la envolvente de lo que cada
          variable ha hecho históricamente. No puedes poner el Euríbor al 40 %
          porque el modelo no está calibrado ahí, y fingir lo contrario sería
          falso.
        </p>
        <div className="tscroll">
          <table className="guide-t">
            <thead>
              <tr>
                <th>Símbolo</th>
                <th>Palanca</th>
                <th>Base</th>
                <th>Rango</th>
                <th>Fuente</th>
              </tr>
            </thead>
            <tbody>
              {LEVER_SPECS.map((s) => (
                <tr key={s.id}>
                  <td className="sym">{s.sym}</td>
                  <td>{s.nm}</td>
                  <td>
                    {nf(BASE_LEVERS[s.id], s.dec)} {s.unit}
                  </td>
                  <td className="dim">
                    {nf(s.min, s.dec)} … {nf(s.max, s.dec)}
                  </td>
                  <td className="dim">{s.src}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card guide-s">
        <h2>4. Cómo viaja un cambio</h2>
        <p>
          Subir el tipo de interés no toca la deuda directamente. Recorre un
          camino, y cada paso tiene un coeficiente con nombre:
        </p>
        <ol className="guide-chain">
          <li>
            Sólo se refinancia el <strong>{nf(C.REFI * 100, 0)} %</strong> de la
            deuda viva cada año (<code>REFI</code>), así que un tipo más alto
            entra en el coste poco a poco, no de golpe.
          </li>
          <li>
            El bono a 10 años se forma como <code>r + TERM + prima/100</code>,
            con <code>TERM = {nf(C.TERM, 2)}</code>.
          </li>
          <li>
            En paralelo, el tipo frena inversión y consumo:{" "}
            <code>E_R = {nf(C.E_R, 2)}</code> puntos de PIB por cada punto de
            tipo, amplificado por el multiplicador fiscal{" "}
            <code>MULT = {nf(C.MULT, 2)}</code> y amortiguado por la persistencia{" "}
            <code>RHO = {nf(C.RHO, 2)}</code>.
          </li>
          <li>
            Menos PIB es menos <code>g</code>, y menos <code>g</code> vuelve a la
            identidad de deuda. El paro sube por Okun{" "}
            (<code>OKUN = {nf(C.OKUN, 2)}</code>) y arrastra a la inflación por
            Phillips (<code>KAPPA = {nf(C.KAPPA, 2)}</code>).
          </li>
        </ol>
        <p>
          Por eso el panel de <Link to="/">Inicio</Link> descompone el
          movimiento palanca a palanca: vuelve a correr el motor con una sola
          palanca movida cada vez y compara. Como los canales se refuerzan entre
          sí, las palancas por separado <strong>no suman</strong> el efecto
          conjunto — y esa diferencia se dibuja como una barra más, en lugar de
          repartirla disimuladamente entre las demás.
        </p>
      </section>

      <section className="card guide-s">
        <h2>5. Cómo leer el abanico</h2>
        <p>
          El escenario determinista traza una línea de {Y0} a {Y1}. Esa línea es
          la parte menos informativa del gráfico. El{" "}
          <Link to="/laboratorio">Laboratorio</Link> añade{" "}
          {nf(4000, 0)} trayectorias Monte Carlo hasta 2070, con choques
          persistentes (AR(1)) sobre el tipo, el crecimiento y el saldo primario.
        </p>
        <p>
          Lo que hay que mirar es <strong>la anchura de la banda</strong>, no la
          mediana. Una mediana tranquila con una banda p5–p95 que se abre en
          abanico significa que el resultado central es poco informativo. La
          semilla está fijada (42), así que dos personas que muevan las mismas
          palancas ven exactamente las mismas bandas.
        </p>
      </section>

      <section className="card guide-s">
        <h2>6. Qué significan las líneas rojas</h2>
        <p>
          Son umbrales anclados a episodios que de verdad ocurrieron, no a
          intuiciones. El estado (<span className="st crossed">cruzada</span>,{" "}
          <span className="st near">cerca</span>,{" "}
          <span className="st safe">segura</span>) se <strong>calcula</strong>{" "}
          desde el escenario en cada año; no hay ningún estado escrito a mano.
          «Cerca» es el {nf(NEAR_FRACTION * 100, 0)} % del umbral.
        </p>
        {redlines.isSuccess ? (
          <ul className="guide-rl">
            {redlines.data.redlines.map((r) => (
              <li key={r.id}>
                <strong>{r.label}</strong> —{" "}
                <span className="dim">{r.source}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="dim">Cargando las definiciones de líneas rojas…</p>
        )}
      </section>

      <section className="card guide-s">
        <h2>7. Qué no puede decirte</h2>
        <ul className="guide-no">
          <li>
            <strong>No es una previsión.</strong> Con todas las palancas en su
            base, lo que ves es la senda central del vintage, no un pronóstico.
          </li>
          <li>
            <strong>Las constantes son calibraciones, no estimaciones.</strong>{" "}
            Vienen de la literatura y de la calibración v16; no se han estimado
            sobre estos datos. Un revisor puede discutirlas, y debería.
          </li>
          <li>
            <strong>No hay política monetaria endógena.</strong> Mueves el tipo a
            mano; el modelo no tiene un banco central que reaccione a la
            inflación que él mismo genera.
          </li>
          <li>
            <strong>No hay ruptura estructural.</strong> Los coeficientes son
            fijos en todo el horizonte, así que el modelo no sabe representar una
            crisis que cambie las reglas del juego.
          </li>
          <li>
            <strong>No es consejo.</strong> Ni de compra, ni de venta, ni de voto.
          </li>
        </ul>
        <p>
          El detalle de fuentes, cortes de datos y huecos conocidos está en{" "}
          <Link to="/metodologia">Datos y método</Link>.
        </p>
      </section>
    </div>
  );
}
