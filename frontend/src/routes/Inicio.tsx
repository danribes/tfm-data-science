import { Link } from "react-router-dom";
import { useMonteCarlo, usePersonas, useRedlines, useVintage } from "../api/hooks";
import { Y1, YEARS, baseline } from "../engine/spain";
import { evaluateRedlines } from "../engine/redlines";
import { REFI } from "../engine/constants";
import { nf, sg } from "../lib/fmt";
import { Caption } from "../components/Caption";
import { DebtVsGdpChart, SnowballStrip } from "../components/DebtVsGdpChart";
import { SpaghettiChart } from "../components/SpaghettiChart";
import { Semaphore } from "../components/Semaphore";
import { Stamp } from "../components/Stamp";
import { SERIES_FORMAT, UP_IS_BAD } from "../components/KpiRow";
import { isFresh, kIndex, useScenario, useScenarioStore } from "../state/scenarioStore";
import { SHIPPED_IDS } from "../personas/registry";
import { DistressGauge } from "../components/DistressGauge";

const HEADLINES: { k: "b" | "saldo" | "u" | "pi"; lab: string; at2050?: boolean }[] = [
  { k: "b", lab: "Deuda", at2050: true },
  { k: "saldo", lab: "Saldo público" },
  { k: "u", lab: "Paro" },
  { k: "pi", lab: "IPCA" },
];

export default function Inicio() {
  const vintage = useVintage();
  const redlines = useRedlines();
  const personas = usePersonas();
  const scn = useScenario();
  const levers = useScenarioStore((s) => s.levers);
  const mc = useMonteCarlo(levers, true);
  const horizon = useScenarioStore((s) => s.horizon);
  const k = kIndex(horizon);
  const base = baseline();
  const fresh = isFresh(levers, horizon);

  return (
    <div>
      <div className="head">
        <h1>España en escenarios</h1>
        <Stamp fresh={fresh} year={horizon} />
        {vintage.isSuccess ? (
          <span className="meta">vintage {vintage.data.vintage} · {nf(vintage.data.n_files, 0)} fuentes congeladas</span>
        ) : vintage.isError ? (
          <span className="meta">cobertura no disponible</span>
        ) : null}
      </div>

      <div className="card">
        <h4>
          El problema de la deuda
          <small>
            {mc.data
              ? `${nf(mc.data.paths.length, 0)} de ${nf(mc.data.n_paths, 0)} trayectorias · semilla ${mc.data.seed}`
              : "trayectorias Monte Carlo"}
          </small>
        </h4>
        {mc.isError && (
          <div className="banner err">
            Monte Carlo no disponible — el resto de la página sigue funcionando.
          </div>
        )}
        {mc.isPending && !mc.data && <p style={{ fontSize: 14 }}>Calculando trayectorias…</p>}
        {mc.data && (
          <SpaghettiChart
            years={mc.data.years}
            paths={mc.data.paths}
            median={mc.data.percentiles.p50}
            /* Only the COVID peak is marked. On an axis that has to reach the
               2070 spread, 105 and 120 sit almost on top of each other and
               their labels collide; the 105 line has its own row in the red
               lines panel below, where it is legible. */
            thresholds={[{ value: 120, label: "120 %PIB · pico COVID 2020" }]}
          />
        )}
        <Caption>
          Cada hebra fina es <strong>un futuro completo y coherente</strong>: la
          misma economía, con los choques de un año arrastrándose a los
          siguientes. No son escenarios que alguien haya elegido, son lo que sale
          de repetir la identidad de deuda miles de veces con perturbaciones
          plausibles. La línea gruesa es la mediana.
        </Caption>
        <Caption>
          Lo que enseña este gráfico no es dónde acaba la mediana, sino que{" "}
          <strong>las hebras no viajan juntas</strong>. Donde se apelotonan, el
          modelo distingue bien; donde se abren en abanico, está diciendo que no
          puede separar futuros muy distintos. Fíjate en que casi ninguna vuelve
          a bajar: la deuda no se devuelve, se diluye con crecimiento o no se
          diluye.
        </Caption>
      </div>

      <div className="outs" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
        {HEADLINES.map(({ k: key, lab, at2050 }) => {
          const i = at2050 ? 24 : k;
          const f = SERIES_FORMAT[key];
          const delta = scn[key][i] - base[key][i];
          const cls = Math.abs(delta) <= 1e-9 ? "" : (delta > 0) === UP_IS_BAD.has(key) ? "bad" : "good";
          return (
            <div className="out" key={key}>
              {/* every tile states its own year: the debt tile is pinned to the
                  end of the projection, the rest read at the selected horizon.
                  Without this a reader sees two different "deuda" magnitudes on
                  one screen (tile vs semáforo) with no obvious explanation. */}
              <div className="o-label">{lab} <small>{at2050 ? Y1 : horizon}</small></div>
              <div className="o-val">{nf(scn[key][i], f.dec)} <small>{f.unit}</small></div>
              <div className={`o-delta ${cls}`}>{sg(delta, f.dec)} vs base</div>
            </div>
          );
        })}
      </div>

      <div className="card">
        <h4>
          Por qué cuesta devolverla
          <small>deuda y economía compuestas desde {YEARS[0]} = 100</small>
        </h4>
        <DebtVsGdpChart scn={scn} years={YEARS} />
        <SnowballStrip scn={scn} k={k} />
        <Caption>
          Las dos curvas salen del mismo punto y crecen a ritmos distintos: la
          deuda se capitaliza al <strong>tipo efectivo</strong> que paga el
          Estado, la economía crece al <strong>PIB nominal</strong>. Mientras el
          crecimiento gane, la deuda se diluye sola aunque no se devuelva un
          euro. Cuando pierde, la zona sombreada — la parte que el crecimiento no
          absorbe — se ensancha cada año por sí sola, sin que nadie gaste más.
          Eso es la bola de nieve, y es la razón de que una deuda se vuelva
          impagable sin ninguna decisión nueva de gasto.
        </Caption>
        <Caption>
          Están en índice y no en euros a propósito: el vintage congelado no trae
          un PIB nominal en euros (<code>gold_bienestar_pais.csv</code> trae PIB
          per cápita en PPS, que es otra unidad), y multiplicarlo daría una cifra
          con aire de oficial que los datos no sostienen. El índice responde igual
          a la pregunta: la distancia entre las curvas <em>es</em> la ratio de
          deuda.
        </Caption>
        <Caption>
          El <strong>7 % del bono a 10 años</strong> es el punto de no retorno
          empírico. No es una ley: es el nivel al que Grecia, Portugal e Irlanda
          pidieron rescate, y que España tocó (7,6 %) en julio de 2012. Importa
          porque es reflexivo — a partir de ahí el mercado exige más precisamente
          porque duda de que puedas pagar, lo que encarece la deuda, lo que
          aumenta la duda. La refinanciación anual del{" "}
          {nf(REFI * 100, 0)} % hace que ese precio tarde años en entrar del todo
          en el coste, pero también que, una vez dentro, tarde años en salir.
        </Caption>
      </div>

      <div className="card">
        <h4>De la macro a tu bolsillo <small>el mismo número, visto desde abajo</small></h4>
        <p className="macromicro-intro">
          Todo lo anterior es agregado: ratios sobre el PIB, décimas de
          crecimiento, puntos básicos. Nada de eso se experimenta directamente.
          Así es como cada magnitud de los gráficos de arriba llega a una
          decisión concreta:
        </p>
        <ul className="macromicro">
          <li>
            <b>Bono a 10 años → tu hipoteca.</b> El coste de la deuda soberana
            marca el suelo del crédito de todo el país. Sube el bono y sube el
            Euríbor al que se revisa la hipoteca variable: la cuota mensual del
            perfil <Link to="/persona/03">🔑 Comprador</Link> sale de ahí, por la
            fórmula francesa.
          </li>
          <li>
            <b>Intereses de la deuda → lo que no se gasta en otra cosa.</b> Los
            puntos de PIB que se van en intereses son gasto que ningún gobierno
            elige: no compiten con otras políticas, van antes que ellas. Es la
            restricción que mira el perfil{" "}
            <Link to="/persona/06">🗳️ Político</Link>.
          </li>
          <li>
            <b>Crecimiento nominal → empleo y salarios.</b> La <code>g</code> de
            la identidad no es una abstracción: por Okun es paro, y por Phillips
            es inflación, que es lo que decide si tu salario sube en términos
            reales o sólo en el recibo.
          </li>
          <li>
            <b>Prima de riesgo → crédito y mora.</b> Un spread más alto encarece
            la financiación de los bancos y endurece la concesión; con más paro
            sube la mora esperada. Es la cadena del perfil{" "}
            <Link to="/persona/02">🏦 Banca</Link>.
          </li>
          <li>
            <b>Indexación y presión demográfica → pensiones.</b> La regla de
            revalorización y la tasa de dependencia deciden cuánto del gasto
            futuro está comprometido antes de empezar a decidir.
          </li>
        </ul>
        <p className="macromicro-intro">
          La dirección también funciona al revés, y es la parte incómoda: las
          decisiones microeconómicas agregadas <em>son</em> la macro. El saldo
          primario es la suma de lo que se recauda y se gasta sobre millones de
          hogares y empresas; el crecimiento es lo que producen. Mover una
          palanca en el panel de la izquierda es suponer que ese comportamiento
          agregado cambia — el modelo te enseña la aritmética de esa suposición,
          no si es realista.
        </p>
      </div>

      <div className="card">
        <h4>Líneas rojas <small>evaluadas en {horizon} · umbrales v12 con fuente</small></h4>
        {redlines.isSuccess ? (
          <Semaphore
            items={evaluateRedlines(redlines.data.redlines, scn, k).map((r) => ({
              title: r.label,
              valueText: nf(r.value, SERIES_FORMAT[r.series]?.dec ?? 1),
              status: r.status,
              note: r.source,
            }))}
          />
        ) : redlines.isError ? (
          <div className="banner err">Líneas rojas no disponibles</div>
        ) : null}
        <Caption>
          Cada umbral está anclado a un episodio que ocurrió de verdad, no a una
          intuición: por eso lleva su fuente al lado. El estado se calcula desde
          el escenario en el año seleccionado — «cerca» es el 10 % del umbral.
          Que una línea aparezca cruzada en la línea base significa que España ya
          está por encima de ese umbral hoy, no que este escenario la haya roto.
        </Caption>
      </div>

      {/* The probabilistic complement of the 7 % threshold, right after the
          thresholds themselves so the two readings sit together. */}
      <DistressGauge />

      <div className="row2">
        {(personas.data?.personas ?? [])
          .filter((c) => SHIPPED_IDS.includes(c.id))
          .map((c) => (
            <Link key={c.id} to={`/persona/${c.id}`} className="card" style={{ textDecoration: "none", color: "inherit" }}>
              <h4>{c.pill}</h4>
              <span style={{ fontSize: 14.5, color: "var(--ink-2)" }}>{c.h1}</span>
            </Link>
          ))}
        {personas.isError && <div className="banner err">Personas no disponibles</div>}
      </div>
    </div>
  );
}
