import { useConstants, useHealth, useRedlines, useVintage } from "../api/hooks";
import { nf } from "../lib/fmt";
import { STALE_LIMIT_DAYS, staleDays } from "../state/appHealth";

const KNOWN_GAPS = [
  "Mora bancaria (NPL, Banco de España): la serie sigue sin conectar — el riesgo de crédito del perfil 🏦 se lee por proxy (paro + colateral).",
  "Bases de cotización del RETA: sin API pública — la senda de la cuota de autónomo no está modelada.",
  "WGI control de la corrupción: API archivada — descarga manual en govindicators.org.",
  "Contratos menores · adjudicación: la señal vive a nivel de contrato, sin serie pública.",
];

export default function Metodologia() {
  const constants = useConstants();
  const redlines = useRedlines();
  const health = useHealth();
  const vintage = useVintage();
  const days = health.data ? staleDays(health.data.vintage) : null;

  return (
    <div>
      <div className="head"><h1>Datos y método</h1>
        <span className="meta">todo lo que se muestra es computado; nada es consejo</span>
      </div>

      <div className="card">
        <h4>Vintage <small>congelado — la app nunca mezcla fechas</small></h4>
        <p style={{ fontSize: 14.5 }}>
          Datos congelados el <b>{health.data?.vintage ?? "…"}</b>
          {vintage.data ? <> ({nf(vintage.data.n_files, 0)} ficheros fuente)</> : null}.
          {days !== null && (days > STALE_LIMIT_DAYS
            ? ` Aviso: el vintage tiene ${nf(days, 0)} días — los datos observados pueden estar desactualizados.`
            : ` Antigüedad actual: ${nf(days, 0)} días (umbral de aviso: ${nf(STALE_LIMIT_DAYS, 0)}).`)}
        </p>
      </div>

      <div className="card">
        <h4>Paridad de motores <small>el mismo número en Python y en el navegador</small></h4>
        <p style={{ fontSize: 14.5 }}>
          El motor TypeScript de esta página pasa el mismo fixture de anclas que el motor Python
          (tests/fixtures/engine_anchors.json, vintage {health.data?.vintage ?? "…"}): senda central de
          deuda 2026/2030/2035/2050 (±10⁻⁶), cuota 2026 (±0,01), 8 presets × 7 series en 2035/2050
          (±10⁻⁶), sonda con las 10 palancas (±10⁻⁶) e identidad contable base (±10⁻⁹). Al arrancar,
          la app además cruza su cálculo local contra POST /scenario y muestra un aviso si difieren.
        </p>
        <p style={{ fontSize: 14.5 }}>
          Monte Carlo se calcula <b>solo</b> en el servidor: los sorteos NumPy PCG64 no son
          reproducibles en JS, así que los pines de semilla 42 del fixture atan al motor Python y la
          regla de aceptación del abanico es la envolvente dorada ±2 pp en 2030/2050/2070.
        </p>
      </div>

      <div className="card">
        <h4>Constantes del motor <small>calibración v16 — defaults declarados, no estimaciones</small></h4>
        {constants.isSuccess ? (
          <table style={{ fontSize: 13.5, borderCollapse: "collapse" }}>
            <thead><tr><th style={{ textAlign: "left" }}>nombre</th><th>valor</th><th style={{ textAlign: "left" }}>unidad</th><th style={{ textAlign: "left" }}>procedencia</th></tr></thead>
            <tbody>
              {constants.data.constants.map((c) => (
                <tr key={c.name}>
                  <td><code>{c.name}</code></td>
                  <td style={{ textAlign: "right" }}>{nf(c.value, c.value < 0.1 ? 4 : 2)}</td>
                  <td>{c.unit}</td>
                  <td style={{ color: "var(--ink-2)" }}>{c.provenance}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : constants.isError ? (
          <div className="banner err">Constantes no disponibles</div>
        ) : null}
        <p className="src" style={{ whiteSpace: "normal" }}>
          Las constantes MC vectoriales (MC_PB_DRIFT y las pendientes de extrapolación) viven solo en
          el servidor: /constants expresa escalares y el abanico nunca se recalcula en el navegador.
        </p>
      </div>

      <div className="card">
        <h4>Líneas rojas globales <small>umbrales v12, con fuente empírica</small></h4>
        {redlines.isSuccess ? (
          <ul style={{ fontSize: 14.5, margin: 0, paddingLeft: 18 }}>
            {redlines.data.redlines.map((rl) => (
              <li key={rl.id}><b>{rl.label}</b> — serie <code>{rl.series}</code>, umbral {nf(rl.threshold, 1)} · {rl.source}</li>
            ))}
          </ul>
        ) : redlines.isError ? (
          <div className="banner err">Líneas rojas no disponibles</div>
        ) : null}
        <p style={{ fontSize: 14.5 }}>
          Los semáforos de cada perfil usan umbrales de <b>presentación</b> propios y nunca se mezclan
          con estas líneas globales. Ejemplo: la fila «Sobrecarga &gt; 40 % renta» del perfil 🔑 evalúa
          la serie <code>sobre</code> contra {nf(15.0, 1)} — el 40 % es la definición Eurostat de
          sobrecarga (porcentaje de la renta), el 15,0 es el umbral sobre la cuota de población que la
          sufre. Estado «cerca» = a menos del 10 % del umbral (0,5 pp absolutos para umbrales en cero).
        </p>
      </div>

      <div className="card">
        <h4>Cómo se generan las explicaciones <small>quién escribe qué</small></h4>
        <p style={{ fontSize: 14.5 }}>
          El panel «Qué está pasando» separa deliberadamente dos cosas: <b>los
          números</b> y <b>las palabras</b>.
        </p>
        <ul style={{ fontSize: 14.5, margin: 0, paddingLeft: 18 }}>
          <li>
            <b>Los números los calcula el motor.</b> El endpoint <code>/explain</code>{" "}
            vuelve a correr <code>engine/spain.py</code> — el mismo motor que fija
            el fixture de anclas — y produce un bloque de hechos: qué palancas se
            han movido, qué series cambian, qué líneas rojas cambian de estado y
            cuánto aporta cada palanca por separado.
          </li>
          <li>
            <b>La descomposición no es una estimación.</b> Para atribuir el
            movimiento se vuelve a correr el motor con una sola palanca movida
            cada vez. Como el motor no es lineal, esas corridas individuales no
            suman el efecto conjunto: la diferencia se publica como término de
            interacción en vez de repartirse entre las palancas.
          </li>
          <li>
            <b>Las palabras las puede escribir un modelo de lenguaje.</b> Los
            hechos se le pasan ya calculados con una instrucción explícita: no
            calcular, no estimar y no citar ninguna cifra que no esté en el
            bloque. El panel indica en cada caso si el texto lo ha redactado el
            modelo o las plantillas deterministas.
          </li>
          <li>
            <b>Si el modelo no está disponible, el texto no desaparece.</b> Hay
            una capa de plantillas deterministas sobre los mismos hechos, que es
            además lo que verifica la suite de tests. La aplicación nunca depende
            de una llamada de red para poder explicarse.
          </li>
        </ul>
        <p style={{ fontSize: 14.5 }}>
          Consecuencia para quien revise este trabajo: cualquier cifra que
          aparezca en un texto explicativo es trazable al motor y reproducible
          desactivando la narración (<code>narrate: false</code>). La redacción
          puede variar entre ejecuciones; los números no.
        </p>
      </div>

      <div className="card">
        <h4>Huecos conocidos <small>lo que falta se declara, no se rellena</small></h4>
        <ul style={{ fontSize: 14.5, margin: 0, paddingLeft: 18 }}>
          {KNOWN_GAPS.map((g) => <li key={g}>{g}</li>)}
        </ul>
      </div>
    </div>
  );
}
