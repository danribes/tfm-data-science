import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  CartesianGrid, Legend, Line, LineChart, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { api } from "../api/client";
import { nf } from "../lib/fmt";
import { useReducedMotion } from "../lib/motion";
import { Caption } from "../components/Caption";

const COLOUR: Record<string, string> = {
  dl_global: "var(--s1)",
  drift: "var(--s2)",
  naive: "var(--muted)",
  snaive: "var(--grid)",
};
const LABEL: Record<string, string> = {
  dl_global: "DL global (candidato)",
  drift: "drift (referencia)",
  naive: "último valor",
  snaive: "naive estacional",
};

export default function Prediccion() {
  const q = useQuery({ queryKey: ["prediction"], queryFn: api.prediction, staleTime: Infinity });
  const reduced = useReducedMotion();

  const data = (q.data?.rows ?? []).map((r) => ({ h: r.h, ...r.mase }));
  const v = q.data?.verdict ?? null;
  const p = q.data?.protocol ?? {};

  return (
    <div className="guide">
      <div className="head">
        <h1>Predicción</h1>
        <span className="meta">
          {q.data?.available ? `protocolo pre-registrado · semilla ${p.seed}` : "sin evaluación"}
        </span>
      </div>

      <section className="card guide-s">
        <h2>Qué se preguntó, y antes de mirar</h2>
        <p>
          La apuesta era razonable: España tiene <strong>un</strong> ciclo
          inmobiliario en la muestra y es justo el que hay que predecir, así que
          un modelo entrenado con datos españoles sólo puede aprender ese ciclo.
          Estados Unidos y Reino Unido aportan décadas de auges y pinchazos
          completos en {nf(Number(p.train_series ?? 1760), 0)} series regionales.
          Si algo puede anticipar un giro, debería ser una red que ha visto morir
          docenas de ellos en otro sitio.
        </p>
        <p>
          La regla para decidirlo se fijó <em>antes</em> de que el modelo
          existiera, y ese es el punto: batir al drift en{" "}
          <strong>{v ? nf(v.required, 0) : 12} de {v ? nf(v.total_ccaa, 0) : 17}</strong>{" "}
          comunidades a un horizonte de un año o menos. Una regla escrita después
          del resultado se puede acomodar al resultado.
        </p>
      </section>

      {q.isError && (
        <div className="banner err">No se pudo leer la evaluación. ¿Está la API en marcha?</div>
      )}
      {q.isPending && <p className="dim">Leyendo la evaluación…</p>}
      {q.data && !q.data.available && <div className="banner">{q.data.note}</div>}

      {q.data?.available && v && (
        <>
          <section className={v.wins ? "card guide-s ok" : "card guide-s"}>
            <h2>Resultado</h2>
            <p className="verdict-line">
              <span className={v.wins ? "st safe" : "st cross"}>
                {v.beaten_ccaa} / {v.total_ccaa} · {v.verdict}
              </span>
            </p>
            <p>
              El candidato gana en <strong>{nf(v.beaten_ccaa, 0)}</strong> de las{" "}
              {nf(v.total_ccaa, 0)} comunidades a h ≤ {nf(v.horizon, 0)}, cuando
              hacían falta {nf(v.required, 0)}. En MASE medio:{" "}
              <strong>{nf(v.mase_candidate, 3)}</strong> frente a{" "}
              <strong>{nf(v.mase_drift, 3)}</strong> del drift — apenas un{" "}
              {nf(((v.mase_candidate / v.mase_drift) - 1) * 100, 1)} % peor, pero
              peor.
            </p>
            <p>
              {v.wins
                ? "La regla se cumple y el candidato pasa a considerarse."
                : "No se han añadido épocas, ni cambiado la arquitectura, ni recortado el horizonte a los trimestres donde sí gana. La regla estaba escrita antes; esto es un resultado, no un contratiempo."}
            </p>
          </section>

          <section className="card guide-s">
            <h2>Error por horizonte</h2>
            <div className="legend">
              {q.data.methods.map((m) => (
                <span key={m}><i style={{ background: COLOUR[m] ?? "var(--ink-2)" }} />{LABEL[m] ?? m}</span>
              ))}
            </div>
            <ResponsiveContainer width="100%" height={300} initialDimension={{ width: 660, height: 300 }}>
              <LineChart data={data} margin={{ top: 12, right: 12, bottom: 4, left: 0 }}>
                <CartesianGrid stroke="var(--grid)" vertical={false} />
                <XAxis dataKey="h" tick={{ fontSize: 13.5, fill: "var(--ink-2)" }}
                  tickLine={false} axisLine={{ stroke: "var(--grid)" }}
                  label={{ value: "trimestres por delante", position: "insideBottom",
                           offset: -2, fontSize: 12, fill: "var(--ink-2)" }} />
                <YAxis width={56} tick={{ fontSize: 13.5, fill: "var(--ink-2)" }}
                  tickLine={false} axisLine={false} tickFormatter={(x: number) => nf(x, 1)} />
                {/* MASE = 1 is the seasonal-naive error. Above it, a method is
                    losing to doing nothing clever at all. */}
                <ReferenceLine y={1} stroke="var(--div-neg)" strokeDasharray="3 3"
                  // Left, not right: at h=8 every line converges on the upper
                  // right and the label lands on top of them.
                  label={{ value: "MASE 1 · naive estacional", fontSize: 11,
                           fill: "var(--div-neg)", position: "insideTopLeft" }} />
                <ReferenceLine x={v.horizon} stroke="var(--grid)" strokeDasharray="2 3"
                  label={{ value: "límite de la regla", fontSize: 11,
                           fill: "var(--ink-2)", position: "top" }} />
                <Tooltip formatter={(x, name) => [nf(Number(x), 3), LABEL[String(name)] ?? String(name)]}
                  labelFormatter={(h) => `h = ${h} trimestres`} />
                <Legend content={() => null} />
                {q.data.methods.map((m) => (
                  <Line key={m} dataKey={m} stroke={COLOUR[m] ?? "var(--ink-2)"}
                    strokeWidth={m === "dl_global" || m === "drift" ? 2.5 : 1.5}
                    dot={false} isAnimationActive={!reduced} animationDuration={200} />
                ))}
              </LineChart>
            </ResponsiveContainer>
            <Caption>
              El candidato y el drift van pegados hasta el año y se separan
              después — al revés de lo que predice un argumento de transferencia.
              Lo que la red aprendió de los ciclos ajenos, si aprendió algo, no
              alcanza a pagar la sencillez de prolongar la pendiente reciente.
            </Caption>
          </section>

          <section className="card guide-s">
            <h2>La tabla completa</h2>
            <div className="tscroll">
              <table className="guide-t">
                <thead>
                  <tr>
                    <th>h</th>
                    {q.data.methods.map((m) => <th key={m} className="num">{LABEL[m] ?? m}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {q.data.rows.map((r) => {
                    const best = Math.min(...Object.values(r.mase));
                    return (
                      <tr key={r.h} className={r.h <= v.horizon ? "" : "dim"}>
                        <td>{r.h}</td>
                        {q.data!.methods.map((m) => (
                          <td key={m} className="num"
                              style={{ fontWeight: r.mase[m] === best ? 800 : 400 }}>
                            {r.mase[m] === undefined ? "—" : nf(r.mase[m], 3)}
                          </td>
                        ))}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <Caption>
              MASE: el error medio dividido por el del naive estacional dentro de
              la muestra de entrenamiento. Por debajo de 1, el método bate a
              repetir el mismo trimestre del año pasado. Las filas en gris quedan
              fuera de la regla y se publican igualmente.
            </Caption>
          </section>

          <section className="card guide-s">
            <h2>Cómo se evitó hacer trampa</h2>
            <ul className="guide-no">
              <li>
                <strong>Nada español en el entrenamiento.</strong>{" "}
                {nf(Number(p.train_windows ?? 0), 0)} ventanas de{" "}
                {nf(Number(p.train_series ?? 0), 0)} series de EE. UU. y Reino
                Unido. Si hubiera una serie española dentro, ganar aquí no
                probaría nada.
              </li>
              <li>
                <strong>Nada posterior a {String(p.train_cutoff ?? "2019Q3")}.</strong>{" "}
                Sólo se usan ventanas cuyo objetivo termina antes del primer
                origen de validación, desde cualquier geografía. Sin ese corte, la
                red habría aprendido la forma del mundo 2020-2023 en Ohio antes de
                que se le pidiera predecirlo en Madrid.
              </li>
              <li>
                <strong>{String(p.test_start ?? "2024Q1")} en adelante, intocado.</strong>{" "}
                El propio arnés descarta cualquier predicción cuyo objetivo caiga
                en el tramo final. No es disciplina del que lo usa: es código.
              </li>
              <li>
                <strong>Ceuta y Melilla fuera, y Nacional sin voto.</strong>{" "}
                Las dos ciudades no tienen ratio de asequibilidad, y por eso el
                denominador de la regla son {nf(v.total_ccaa, 0)}. Nacional
                agrega las mismas regiones: contarlo sería puntuar dos veces parte
                del panel.
              </li>
            </ul>
            <p className="caption">
              Orígenes {String(p.origins ?? "")} · horizontes 1–{nf(Number(p.horizons ?? 8), 0)} ·
              semilla {String(p.seed ?? 42)}. La evaluación se calcula fuera de
              línea (<code>python -m research.dl_global</code>) y se versiona con
              el repositorio: entrenar la red cuesta minutos y una página que la
              reentrenara en cada visita sería más lenta que informativa.
            </p>
          </section>

          <section className="card guide-s">
            <h2>Qué se hace con esto</h2>
            <p>
              Nada, en producción. Los escenarios que ves en{" "}
              <Link to="/">Inicio</Link> y en{" "}
              <Link to="/laboratorio">Laboratorio</Link> siguen saliendo del motor
              estructural, no de esta red. Un candidato que no pasa la regla no
              entra, y publicar el intento fallido es más informativo que no haber
              intentado nada: dice cuánto margen hay realmente sobre una
              extrapolación simple en una serie con tanta inercia como el precio
              de la vivienda.
            </p>
            <p className="caption">
              La comparación con la calibración estructural vive en{" "}
              <Link to="/evidencia">Evidencia</Link>, que hace la pregunta
              contraria: no si un modelo predice mejor, sino si las constantes que
              usa el motor son compatibles con los datos.
            </p>
          </section>
        </>
      )}
    </div>
  );
}
